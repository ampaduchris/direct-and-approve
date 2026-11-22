# quantity specification (synthetic)

| Id | Level | Requirement | Test |
| --- | --- | --- | --- |
| REQ-001 | MUST | `parse_quantity(text)` returns the whole number written in the text. Spaces around it are ignored. | `test_quantity_read` |
| REQ-002 | MUST | Zero or a negative number raises `ValueError`. | `test_zero_and_negative_rejected` |
