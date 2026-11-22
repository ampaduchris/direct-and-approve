# settings specification (synthetic)

| Id | Level | Requirement | Test |
| --- | --- | --- | --- |
| REQ-001 | MUST | `load_settings(text)` reads `key = value` lines into a dictionary of strings. Blank lines and lines that begin with `#` are ignored. | `test_keys_and_values_read` |
| REQ-002 | MUST | A line without `=` raises `ValueError` and the message names the line number. | `test_bad_line_names_its_number` |
