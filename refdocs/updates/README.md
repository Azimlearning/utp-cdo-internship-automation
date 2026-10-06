# Flow Updates: the one place to look

Everything about the per-flow fix work is reachable from here. Start with **[FLOW-TRACKER.md](FLOW-TRACKER.md)**: one row per flow, with status, links and the next action.

| File | What it is | Audience |
|---|---|---|
| [FLOW-TRACKER.md](FLOW-TRACKER.md) | Live status of all 14 flows (found → fix built → sandbox tested → office-ready → applied) | You, and Claude at session start |
| [MANUAL-TODO.md](MANUAL-TODO.md) | Everything only you can do (checks, CDO questions, office tests, decisions) | You |
| [ISSUES-BY-FLOW.md](ISSUES-BY-FLOW.md) | Every known issue, which flow it comes from, evidence level and fix status | You, your supervisor |
| `YYYY-MM-DD-flow-fixes-progress.md` | Plain-language progress updates for your supervisor / CDO staff | Stakeholders |

**Where the detail lives** (linked from the tracker, not duplicated here):

- Per-flow findings, fix and test results: `../issues/YYYY-MM-DD-flow-NN-*.md`
- Test evidence screenshots: `../issues/evidence/flow-NN/`
- Fix code and package builder: `../../tools/` (`fixes/fNN_*.py`, `build.py`)
- How to run a sandbox test: `../guides/sandbox_runbook.md`

**Rule:** when a flow's status changes, update its row in FLOW-TRACKER.md in the same session, then add to the latest progress update. The changelog and STATUS.md stay as the session log and phase view.
