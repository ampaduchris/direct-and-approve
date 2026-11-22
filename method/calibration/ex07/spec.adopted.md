# digits specification (synthetic)

| Id | Level | Requirement | Test |
| --- | --- | --- | --- |
| REQ-001 | MUST | `hide_digits(line)` replaces every digit in the line with `#`. | `test_no_digit_survives` |
| REQ-002 | MUST | A line without digits is returned unchanged. | `test_line_without_digits_unchanged` |
