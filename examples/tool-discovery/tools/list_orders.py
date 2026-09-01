"""A read tool: looks up a fixed order list, changes nothing."""

NAME = "list_orders"
ACCESS = "read"
DESCRIPTION = "List open orders for a customer. Read-only."

_ORDERS = {
    "cust-1": ["order-101", "order-102"],
    "cust-2": ["order-201"],
}


def run(arguments: dict) -> list:
    return _ORDERS.get(arguments.get("customer_id", ""), [])
