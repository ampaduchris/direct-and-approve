# redact specification (synthetic)

| Id | Level | Requirement | Test |
| --- | --- | --- | --- |
| REQ-001 | MUST | `redact(text, terms)` replaces every occurrence of every term with `[X]`, ignoring case, and returns the result under the key `text`. | `test_redact_report, test_redact_two_terms` |
| REQ-002 | MUST | The value under the key `count` equals the number of replacements made. | `test_redact_report` |
