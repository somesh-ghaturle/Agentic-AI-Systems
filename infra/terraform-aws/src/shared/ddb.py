# DynamoDB type marshalling, both directions.
#
# DynamoDB has no float. boto3's serializer refuses one outright —
#
#   TypeError: Float types are not supported. Use Decimal types instead.
#
# — and every value written here originates outside our control: the arguments a model
# proposed, the JSON a write tool returned, the approver object a callback supplied. Any
# of them can carry a decimal. Unnormalized, the write raises and the approval record is
# never written, which is the one record the system cannot afford to lose.
#
# Reading back has the mirror problem: DynamoDB returns every number as Decimal, which
# json.dumps refuses to serialize.

import decimal

# DynamoDB stores up to 38 significant digits. Beyond that a write is rejected, so bound
# the context rather than let boto3 raise on a value we could have rounded.
_CONTEXT = decimal.Context(prec=38)


def to_item(value):
    """Normalizes a value for writing to DynamoDB.

    Decimal(str(x)) rather than Decimal(x): the latter preserves binary floating-point
    artifacts, turning 0.1 into 0.1000000000000000055511151231257827 and burning the
    38-digit budget on noise.
    """
    if isinstance(value, bool):
        # Before the int check — bool is a subclass of int, and DynamoDB has a real
        # boolean type worth keeping.
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            # DynamoDB rejects non-finite numbers. Keep the record writable and let the
            # value survive as text: an audit record with "NaN" in it beats no record.
            return repr(value)
        return _CONTEXT.create_decimal(str(value))
    if isinstance(value, dict):
        return {k: to_item(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_item(v) for v in value]
    return value


def from_item(value):
    """Normalizes a value read out of DynamoDB back into plain JSON-serializable types."""
    if isinstance(value, decimal.Decimal):
        as_int = int(value)
        return as_int if as_int == value else float(value)
    if isinstance(value, dict):
        return {k: from_item(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [from_item(v) for v in value]
    return value
