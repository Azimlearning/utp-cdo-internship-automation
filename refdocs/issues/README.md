# Issues

> One file per backlog item from `refdocs/guides/issues_backlog.md`, opened when work on that item starts. This is the **narrative home** for an issue — analysis, review, and fix design in one readable place — and it links out to the full plan/execution pair in `refdocs/plans/` and `refdocs/execution/` rather than duplicating their detail.
>
> Relationship to the rest of the doc system: `issues_backlog.md` is the flat list of everything known; a file in here is opened for the one item currently being worked; `plans/` + `execution/` carry the formal what/why and how/order once the issue is ready to execute. Keep them in sync — if the fix design changes here, it changes in the plan/execution pair too, same session.

## Naming convention

`YYYY-MM-DD-<NN>-<slug>.md` — date opened, the item's number from `issues_backlog.md`, then a short kebab-case slug.

## Required sections

1. **Status** — one line, updated every session this issue is touched
2. **Reported symptom** — in the user's own words, from the original brief
3. **Analysis** — root cause, with evidence (a `grep` result, a specific `definition.json` excerpt) — not a guess
4. **Review** — what already exists and works, that the fix must not break; anything the analysis phase changed about the original assumption
5. **Fix design** — the concrete approach, precise enough to execute without follow-up questions (this is a no-Claude-on-site project — see CLAUDE.md rule 6)
6. **Plan / execution links**
7. **Verification** — how we'll know it actually worked, observed not assumed

## Index

| File | Issue # | Status |
|---|---|---|
| [2026-09-16-01-no-failure-notifications.md](2026-09-16-01-no-failure-notifications.md) | 1 | In progress |
