# Plans

> **MANDATORY:** Before implementing any non-trivial feature — or, for this project, before any office-laptop session that edits a live flow — a plan document must exist in this folder.
> A plan covers **what** and **why** — goal, scope, constraints, risks, definition of done.
> The **how** and **in what order** belongs in `refdocs/execution/`. When the two merge, both stop being read.

## Naming convention

`YYYY-MM-DD-<slug>.md` — the date the plan was written, then a short kebab-case slug.

**The execution doc uses the identical filename** in `refdocs/execution/`. Same date, same slug — that mirroring is how you find a plan's other half without opening anything. If a plan gets superseded, write a new one and mark the old row Superseded; don't rewrite history in place.

## Required sections in every plan

1. **Why this exists** — the problem, in the user's terms
2. **What's already covered** — what needs no work, so nobody rebuilds it
3. **Scope** — what's in, and what's explicitly out *with reasons*
4. **Approach** — the shape of the solution
5. **Risks & unknowns** — with honest confidence levels. "I read the flow's actual `definition.json`" and "I think this flow does that" are different rows.
6. **Definition of done** — phrased as observable facts, not intentions

## Index

Add a row when you write a plan. Update the status when it moves — a stale index is how a project ends up with three plans for the same thing.

Status vocabulary: `Draft` · `In progress` · `Done` · `Blocked` · `Superseded` · `On hold`

| File | Description | Status |
|---|---|---|
| [2026-09-16-observability-and-error-handling.md](2026-09-16-observability-and-error-handling.md) | P2 target: add failure-path error handling + Teams alerts to all 14 flows | Superseded (2026-09-30) |
| [2026-10-02-real-system-rollout.md](2026-10-02-real-system-rollout.md) | P2 + P3 together: apply the sandbox-tested fixes to the real system by waves, probe-test the alert path, prove the rest on test data or the first genuine run | Draft |

**Still to write:** a plan for the path-based Excel lookup fix (D-03, issue 2) and a mini-plan for flow 2 (trigger swap, approvals, letters) — the rollout plan above leaves both out on purpose.
