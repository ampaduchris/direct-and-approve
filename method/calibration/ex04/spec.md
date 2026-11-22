# cards specification (synthetic)

| Id | Level | Requirement | Test |
| --- | --- | --- | --- |
| REQ-001 | MUST | `mask_card(number)` replaces every digit except the last four with `*`. Every other character is kept in place. | `test_all_but_last_four_masked` |
| REQ-002 | MUST | A number with fewer than 12 digits raises `ValueError`. | `test_short_number_rejected` |
