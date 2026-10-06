---
description: Write the plan + execution doc pair required before editing any live flow
argument-hint: [which fix or phase you want to plan]
allowed-tools: Read, Write, Glob, Grep, Bash
---

Produce the plan/execution pair CLAUDE.md requires before any live flow edit, for: $ARGUMENTS

First read `refdocs/STATUS.md`, the PRD, `refdocs/changelog/DECISIONS.md`, and `refdocs/guides/flow_inventory.md`, plus the actual flow(s) this would touch (extract the relevant `.zip` from `flows/`). Check whether an existing plan already covers it — if so, say so instead of writing a duplicate.

Write two files, matching the structure of `refdocs/plans/2026-09-16-observability-and-error-handling.md` and its execution companion — that pair is this project's reference example:
- `refdocs/plans/YYYY-MM-DD-<slug>.md` — what and why: scope in/out with reasons, approach, a risk table with honest confidence levels (grounded in what was actually read from the flow's JSON, not assumed), and a definition of done phrased as observable facts.
- `refdocs/execution/YYYY-MM-DD-<slug>.md` — how and in what order: numbered tasks naming the exact flow(s) and Studio steps, each carrying its own **Verify** step with a real test and expected result.

Respect D-02 (fit one office-laptop session, or say explicitly it needs more) and D-03 (any Excel template edit must be in-place, never a replacement — flag it loudly if it isn't).

Do not implement anything or touch a live flow. Return both paths and the task order.
