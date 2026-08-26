# Shared accessors over conftest's hcl2 parse tree.
#
# Under `--combine`, `input` is an array of `{path, contents}` — one entry per file, with
# `contents` holding the parsed HCL. Combining is what makes these policies possible: the
# resource that declares a control and the resource that wires it are routinely in different
# files, and a per-file pass can only ever see half of that.
#
# The parser preserves interpolations verbatim, so `rai_policy_name` arrives as the literal
# string `${var.x ? azurerm_...guardrail[0].name : null}`. That is why wiring is checked by
# substring rather than by resolving the expression: nothing here evaluates HCL, and a
# reference that appears anywhere in the expression is a reference.

package main

import rego.v1

# Names of every resource block of `kind`, across every file in the combined input.
resource_names(kind) := {name |
	some i
	some name, _ in object.get(input[i], ["contents", "resource", kind], {})
}

# Every string value of attribute `attr` on every resource of `kind`.
attr_strings(kind, attr) := {value |
	some i
	some _, blocks in object.get(input[i], ["contents", "resource", kind], {})
	some block in blocks
	value := block[attr]
	is_string(value)
}

# True when any expression in `refs` mentions `target`.
references(refs, target) if {
	some ref in refs
	contains(ref, target)
}

# Every string value of `attr` on a nested block `block_name` inside resources of `kind`.
#
# The hcl2 parser represents a nested block as a list of objects under the block's name, so
# `on_schema_object { object_name = ... }` is not reachable by attr_strings — which only
# sees the resource's own attributes. Snowflake puts the thing every grant is *about*
# inside such a block, so wiring checks on that provider need this.
nested_attr_strings(kind, block_name, attr) := {value |
	some i
	some _, blocks in object.get(input[i], ["contents", "resource", kind], {})
	some block in blocks
	some nested in object.get(block, [block_name], [])
	value := nested[attr]
	is_string(value)
}
