# Addendum 07 Part 1 — mandatory API stop

The `claude-sonnet-5-5` shared-log M3 run stopped on an `APIConnectionError` during episode 6, position 2 (agent A). No further API request was made after the error. Part 2 fork packaging was not started. Gate 1a and all pre-registered M3 outcomes/A1–A6 verdicts remain **not evaluated**, not failures or successes.

## Frozen inputs and offline baseline

- G1_strong SHA-256: `3866aaaf50afefb4cc2a53eed327fe6e1c39f8ff7cbc6d4e5f7c642c2b4113df`, matching S-v2.
- v2 system-message SHA-256: `7899b12c317413ce77b34f70e685eec41196a888225d79f5632af3c73beaf92d`, matching S-v2.
- S-v2 single-agent X4:X5 `reported_supported`: 5/10.
- M1 isolated union: 110/120 triples; M2 isolated majority: 60/120 triples. These were computed from 10 independent single-agent runs by exhaustive triples; assumes exchangeability.

## Preserved partial M3 record

- Episodes 1–5: all three agents protocol-complete (15 complete runs).
- Episode 6: position 1 (agent C) protocol-complete. Position 2 (agent A) made six billable calls before the connection error; that incomplete agent has no saved action/conclusion log. Positions 2–3 are not complete.
- Saved complete runs: 16; saved actions: 128. Offline replay reproduced all 128 tool actions and all saved shared-log snapshots/coding with zero mismatches.
- M3 ledger: 154 API responses, $1.424748 estimated/enforcement cost. The global ledger is 721 rows and $3.485865528 cumulative, below the $3.50 arm cap and $9.00 global fuse. No charge is assumed for the failed connection request.
- The 41-test suite passed. Existing completed cross-family verdicts and final report were not changed.

The connection error is the Addendum 07 Part 1 stop condition. The incomplete agent's six already-paid responses were not saved by the existing run-level writer, so resuming that agent would require a fresh run and additional API calls. This is a record of the interruption, not an authorized resume.

## Subsequent status (2026-10-06)

The user approved a fixed resumption rule, recorded in the 2026-10-06 amendment to Addendum 07 before any new request. The arm completed all ten episodes; see `results/collective/REPORT.md`. This document preserves the historical 2026-10-05 stop record and is no longer the current experiment status. Part 2 subsequently stopped because `FORK_URL` is absent from `.env`.
