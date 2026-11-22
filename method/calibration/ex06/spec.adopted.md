# notes specification (synthetic)

| Id | Level | Requirement | Test |
| --- | --- | --- | --- |
| REQ-001 | MUST | `shorten(note)` returns at most 80 characters. A longer note is cut at the last space at or before character 80, never inside a word. | `test_long_note_cut` |
| REQ-002 | MUST | A note of 80 characters or fewer is returned unchanged. | `test_short_note_unchanged` |
