# Preflight — UTP CDO Internship Automation Session Start

> Read this at the start of every session, before touching anything.
> One page, six questions, then you can build. CLAUDE.md is the reference; this is the gate.

---

## 1. Where are we?

Open `refdocs/STATUS.md`. Find the current phase and the one next action.
If STATUS's claims and a flow's actual behavior in Power Automate disagree, **that's the session's first task** — not the thing you were about to do.

---

## 2. Which component am I about to touch, and do I have the access this session actually has?

| Component | Where it lives | This session can touch it if... |
|---|---|---|
| PowerApp | Power Platform environment | You have Power Apps Studio access — not exported into this repo |
| Power Automate flows (13) | `flows/*.zip` here, live in Power Automate | **Reading/planning:** any session. **Live editing:** only at the office admin laptop (hard constraint) |
| SharePoint Lists / Excel templates | `CareerDevelopmentOfficeCDO` site | Same as flows — live changes need the office admin laptop |
| Docs (`refdocs/`, `CLAUDE.md`, this file) | This repo | Any session, always |

**If this is a personal-account session:** you can read, extract, analyze, write plan/execution docs, and **build + test sandbox copies** (D-08, `refdocs/guides/sandbox_runbook.md`) — you cannot make a live change stick. Don't simulate having made a fix; a sandbox pass is "fix design verified", not "production fixed".

---

## 3. Does a plan exist for what I'm about to build?

Live flow edit → a plan doc in `refdocs/plans/` **and** an execution doc in `refdocs/execution/` must exist first. If neither exists, write them (`/plan-feature`). If one exists but reality has moved (a flow was already partially fixed, a new gap was found), update it before building on it.

---

## 4. Has this already been decided?

Skim `refdocs/changelog/DECISIONS.md` before re-opening an architectural choice — especially D-03 (Excel templates cleared in place, never replaced) and D-02 (batched office-laptop sessions). If your plan contradicts an ADR, you need a new ADR that says why — not a silent reversal.

Check the open `ASSUMED:` list at the bottom of that file. If today's work is load-bearing on one of them (e.g., you're about to edit "Email for Student Report Duty Status" — its name/content mismatch is still unconfirmed), **confirm it before you build**, not after.

---

## 5. Am I about to touch an Excel master-list template, or a flow that references one by a fixed ID?

This project's real trap, confirmed by direct inspection (D-03): Office Scripts and `Get_file_content_using_path` actions in flows #2, #7, #12, #13 reference their Excel `.xlsx` template by a hard-coded SharePoint drive-item ID and Office Script ID, bound to that specific file object. **If the file is ever deleted and re-uploaded — even with an identical name — every flow referencing it breaks, silently, with no error until someone notices a downstream failure.**

Before any semester-rollover action, any "let me just clean up this file" action, or any fix from P3: confirm you are editing/clearing the *existing* file in place, not creating a replacement. If you must replace a template file for a real reason, that's a load-bearing exception — write an ADR, and update every ID in `guides/env_setup.md` and every flow that references it, in the same session.

---

## 6. Will I close the session properly?

`/session-end` — changelog entry, STATUS phase table, verification ledger, any new ADR.
The changelog entry is mandatory after any session that changed a flow, made a decision, or modified a plan. Even a one-line fix gets a one-line entry.

---

## Quick links

| Doc | Purpose |
|---|---|
| `refdocs/STATUS.md` | Where the build actually is |
| `CLAUDE.md` | Operating brief — rules, constraints, stack |
| `refdocs/cdo-internship-automation-PRD.md` | Scope, architecture, roadmap, decision log |
| `refdocs/changelog/DECISIONS.md` | Settled calls — read before re-debating |
| `refdocs/guides/flow_inventory.md` | Every flow's trigger/connectors/purpose |
| `refdocs/guides/env_setup.md` | Site URLs, item IDs, connection owner |
| `refdocs/guides/checklist.md` | Pre-change checklist for live edits |
| `refdocs/plans/` · `refdocs/execution/` | What/why · how/in what order |
