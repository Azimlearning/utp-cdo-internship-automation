# Execution Plans

> **MANDATORY:** Every plan in `refdocs/plans/` that moves to implementation must have a matching execution document here.
> An execution plan covers **how** and **in what order** — ordered tasks, file paths (or, for this project, flow names + Studio actions), commands, and a Verify step per task.
> Do not start an office-laptop session for a plan that has no execution doc. Write one first.

## Naming convention

`YYYY-MM-DD-<slug>.md` — **identical filename to its companion plan** in `refdocs/plans/`. Same date, same slug.

## Required sections in every execution plan

1. **Companion plan** — link to the plan doc, at the top
2. **Before starting** — preconditions, access needed, what must already be green
3. **Tasks** — ordered and self-contained, each with:
   - the flow(s) it touches
   - the exact Studio steps
   - a **Verify** step: what was actually run and its expected result
4. **Wrap-up** — the STATUS / changelog / ADR checklist

**A task is done when its Verify passes** — not when the flow saves without error in the designer. That distinction is the entire value of this folder.

## Keeping these honest

If reality diverges from the doc mid-session, **edit the doc** and note it in the changelog's Deviations line. A plan that changed silently is a plan nobody trusts next time.

## Index

| File | Companion plan | Status |
|---|---|---|
| [2026-09-16-observability-and-error-handling.md](2026-09-16-observability-and-error-handling.md) | [../plans/2026-09-16-observability-and-error-handling.md](../plans/2026-09-16-observability-and-error-handling.md) | Superseded (2026-09-30) |
| [2026-10-02-real-system-rollout.md](2026-10-02-real-system-rollout.md) | [../plans/2026-10-02-real-system-rollout.md](../plans/2026-10-02-real-system-rollout.md) | Not started |
