# luhn specification (synthetic)

| Id | Level | Requirement | Test |
| --- | --- | --- | --- |
| REQ-001 | MUST | `luhn_ok(digits)` returns `True` exactly when the Luhn checksum of the digits is 0 modulo 10: starting from the rightmost digit, every second digit is doubled, and 9 is subtracted from any doubled value above 9. | `test_luhn_checksum` |
| REQ-002 | MUST | A string that contains any character other than a digit returns `False`. | `test_non_digits_rejected` |
