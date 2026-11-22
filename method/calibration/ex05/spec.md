# cents specification (synthetic)

| Id | Level | Requirement | Test |
| --- | --- | --- | --- |
| REQ-001 | MUST | `to_cents(text)` converts a decimal amount with zero, one or two decimal places to whole cents: `12.34` gives 1234, `12.5` gives 1250, `7` gives 700. | `test_to_cents` |
| REQ-002 | MUST | More than two decimal places raises `ValueError`. | `test_third_decimal_rejected` |
| REQ-003 | MUST | A negative amount keeps its sign: `-0.05` gives -5. | `test_to_cents` |
