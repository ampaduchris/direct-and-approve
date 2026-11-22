# Build 00: wordcount-example (a synthetic example)

This build is invented to show the format. It does not describe a real project and no repository of this name exists.

**Pitch:** A command-line tool that counts the words in a text file and prints the count.

**Why here:** it is small enough that its two sessions fit on this page.

## Scope v1.0
- S1 Count: `wordcount <file>` prints the number of words, where a word is a run of non-space characters.
- S2 Errors: a missing file exits 2 with one line on stderr.

Out of scope: other languages, a package on PyPI.

## Stack
Python 3.11+ standard library; pytest. MIT licence.

## Test plan
| Layer | What | Target | Tool |
| --- | --- | --- | --- |
| Unit | Counting on five inputs, including empty and one word | 5 cases | pytest |
| Failure | Missing file exits 2 | 1 case | pytest |

## Release checklist
- [ ] All MUSTs traced and passing
- [ ] CI green
- [ ] README with the claim and three commands that reproduce it
- [ ] CHANGELOG, tag v1.0.0, release
