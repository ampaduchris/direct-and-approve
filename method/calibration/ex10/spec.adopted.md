# stats specification (synthetic)

| Id | Level | Requirement | Test |
| --- | --- | --- | --- |
| REQ-001 | MUST | `median(values)` returns the middle value of an odd number of values. | `test_odd_count` |
| REQ-002 | MUST | For an even number of values it returns the mean of the two middle values. | `test_even_count` |
| REQ-003 | MUST | An empty list raises `ValueError`. | `test_empty_rejected` |
