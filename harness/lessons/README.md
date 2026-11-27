# Lesson texts (Notes block)

Copied verbatim (after `.strip()`, exactly as the Gemma text rows used them in `demo/gen_textrows.py:row_texts`) for the harness `notes` solver:

| file | source | role |
| --- | --- | --- |
| method_original.txt | `demo/textrows.py` METHOD | our written rule (the "method" paragraph) |
| teacher.txt | `demo/gen/teacher_method.txt` (frozen, sha256 of the file f41ae9b3...) | Claude's lesson (teacher loop, round 1) |
| neutral.txt | `demo/gen/neutral_text.txt` | same-length neutral control |
| wrong_rule.txt | `demo/textrows.py` FIXED["wrong_rule"] | wrong-rule control |

`tests/harness/test_lessons.py` checks that each file still equals its source.
