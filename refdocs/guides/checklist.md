# Pre-Change Checklist — UTP CDO Internship Automation

> Run the relevant section before editing a live flow, or calling a phase done. This is a Power Platform low-code project — there is no build/CI/lint in the traditional sense. "Verify" here means *actually ran the flow in Power Automate Studio and read its run history*, not "the JSON looks right."

---

## Every change to a live flow

- [ ] **A fresh `.zip` backup was exported from Studio and saved into `flows/` *before* editing** — this is the project's only rollback mechanism (D-07). Don't edit, then export; export first.
- [ ] **It was actually run in Power Automate Studio's test mode**, not just saved. Check the run history for the specific run, not just "no red X in the designer."
- [ ] **A deliberately-forced failure was tested** where the change touches error handling (P2) — trigger the failure path on purpose and confirm the Teams alert actually posts.
- [ ] **No hard-coded drive-item ID or Office Script ID was introduced or left unexamined** where the change touches an Excel-referencing flow (D-03). If one is unavoidable, it's recorded in `guides/env_setup.md`.
- [ ] **Changelog entry added** — `refdocs/changelog/CHANGELOG.md`, with an honest **Verified** line naming the actual test run and its result.
- [ ] **STATUS.md reflects reality** — the phase table doesn't round up, and the verification ledger has a row for what was actually run in Studio.
- [ ] **`guides/flow_inventory.md` updated** if the change touched a flow's trigger, connectors, or purpose — that file is the ground-truth map and goes stale fast otherwise.
- [ ] **Docs match what you built** — if the work diverged from the execution doc, that doc is edited, not left stale.

---

## Architectural decision

- [ ] ADR added to `refdocs/changelog/DECISIONS.md` — Decision → Why → Trade-offs/rejected
- [ ] Same id added to the PRD's §7 Decision Log
- [ ] Any `ASSUMED:` it resolves is deleted from the PRD §8 / DECISIONS.md assumptions list

---

## Before turning a fixed flow back on (replaces "before deploy" — there is no separate deploy step; turning the flow on/off in Studio *is* the deploy)

- [ ] Confirmed with whoever's at the admin laptop that this is an office-laptop session (P2/P3/P4), not a remote/personal-account attempt at a live edit — live changes require physical admin access (see PRD §1 constraints)
- [ ] The flow's manual-trigger schema (if changed) still matches what the PowerApp actually sends — a mismatch here fails silently on the PowerApp side, not the flow side
- [ ] Teams success *and* failure notifications both confirmed firing for this specific flow, not assumed from another flow's fix
- [ ] `guides/env_setup.md` updated if any drive-item ID, folder path, or connection owner changed as part of this fix

---

## End of an office-laptop session (P2 / P3 / P4)

- [ ] Every flow touched this session is listed in the changelog entry, with its individual Verify result — not a single "fixed the flows" line
- [ ] STATUS.md phase table updated for the phase this session covered
- [ ] Any flow *not* finished this session is explicitly marked ⛔ Blocked or 🔶 In progress in STATUS.md, naming what's left — never left silently implying it's done
