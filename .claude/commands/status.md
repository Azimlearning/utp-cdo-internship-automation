---
description: Where is this project actually at?
allowed-tools: Read, Glob, Grep, Bash
---

Tell me where this project actually stands.

Read `refdocs/STATUS.md`, the last few `refdocs/changelog/CHANGELOG.md` entries, and any in-progress execution doc. Then check reality: `git log --oneline -10`, `git status`, and whether `flows/` has any `.zip` newer than what STATUS.md's verification ledger accounts for.

Report:
- Current phase and what's genuinely done vs claimed done
- Anything STATUS.md says is ✅ that the verification ledger or `guides/flow_inventory.md` doesn't support — flag this loudly, it's the failure mode this file exists to catch
- Open `ASSUMED:` items and blockers (including whether the next action needs the office admin laptop)
- The single next action

Be blunt about drift. An accurate "STATUS is ahead of reality in two places" is the whole point of running this.
