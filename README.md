# Concordia scaffold study

Protocol and reference implementation for a pre-registered study of the top three NeurIPS 2024 Concordia Contest agents on Gemma 2 9B-it: do their reasoning texts lower regret in a haggling decision with a known best offer, and can the effect be reproduced by an activation-steering direction?

- `PROTOCOL.md`: the experiment protocol (authoritative).
- `REFERENCE.md`: overview, code listing and test results for the reference implementation.
- `refimpl/`, `tests/`: the reference implementation and its tests.
- `requirements.lock`: pinned Python 3.11 environment (CPU torch; GPU runs use torch 2.4.1 from PyPI).
- `STAGE1_PROMPT.md`: instructions for the first GPU run (setup, 9B checks, formative memories, registration package).

Contest agent code is not redistributed here; it is downloaded from the NeurIPS supplementary archive and verified by SHA-256 (see `PROTOCOL.md` section 3).
