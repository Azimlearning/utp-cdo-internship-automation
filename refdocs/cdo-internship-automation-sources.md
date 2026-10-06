# UTP CDO Internship Automation — Sources & References

> Raw research and external dependencies. The PRD is the *decided* view; this file is the *considered* view.

Last updated: 2026-09-16

---

## Founding context documents

The documents this project was scaffolded from. Kept because the PRD paraphrases them and paraphrase loses detail.

- [`context-2026-09-16-brief.md`](context-2026-09-16-brief.md) — the raw requirements brain-dump given in chat, plus the follow-up access/deadline/scope answers
- [`context-2023-2024-admin-user-guide.pdf`](context-2023-2024-admin-user-guide.pdf) — the original system's admin user guide (30 Oct 2023 – 11 Jun 2024), by Chew Jing Ye, the CDO intern who built/documented it before Kamal's tenure as admin. Notes: [`guides/previous_system_guide_notes.md`](guides/previous_system_guide_notes.md)
- [`guides/flow_inventory.md`](guides/flow_inventory.md) — every fact in this doc set about the 14 flows traces back to this file, which traces back to the actual exported `.zip` contents in `flows/`

## External services this project depends on

| Service | Used for | Pricing model | Auth / connection | Status |
|---|---|---|---|---|
| SharePoint Online (`utpmy.sharepoint.com/sites/CareerDevelopmentOfficeCDO`) | Student/company lists, Excel master-list templates, letter drop folders | Included in UTP's M365 tenant | Power Automate SharePoint connector, currently under `kamalazreel.k@utp.edu.my` | Live, in active use |
| Excel Online (Business) | Master-list reconciliation, raw-data staging, via Office Scripts (`Run script` / `RunScriptProd`) | Included in UTP's M365 tenant | Power Automate Excel Online connector, same account | Live, in active use — see D-03 for its known fragility |
| Office 365 Outlook | Confirmation, reminder, bulk, and acknowledgement-letter emails | Included in UTP's M365 tenant | Power Automate Outlook connector, same account (personal mailbox — see M6) | Live, in active use |
| Microsoft Teams | Processing/success notifications (`PostMessageToConversation`) | Included in UTP's M365 tenant | Power Automate Teams connector, same account | Live, success-path only (see M7 gap) |
| Word Online (Business) | Generates the appointment/acknowledgement letter document | Included in UTP's M365 tenant | Power Automate Word Online connector | Live, used only in the Acknowledgement Letter flow |
| Standard approvals (Power Automate built-in) | An approval step inside the Acknowledgement Letter flow | Included, no separate license | Built-in Power Automate connector | Live — purpose not yet confirmed, see PRD Open Question #4 |

No third-party (non-Microsoft) services are used anywhere in this system. No API keys exist — all auth is Microsoft OAuth connections managed inside Power Automate. This is why the project has no `.env.example` (see D-05).

## Reference material

- Microsoft's own deprecation notice for the "When a file is created in a folder (deprecated)" SharePoint trigger — not yet pulled into this repo verbatim; worth fetching before P3 to cite the exact replacement action Microsoft recommends and any migration gotchas.
- Office Scripts identity/permissions model (who a `Run script` action executes as, and whether that changes when the file's SharePoint permissions or the flow's owning account changes) — not yet researched; directly relevant to M6 (ownership migration) and flagged as PRD Open Question #4-adjacent risk in the P4 plan once it's written.

## Considered and rejected

| Option | Why it looked good | Why it lost | Recorded in |
|---|---|---|---|
| Full rebuild on a custom web app + database | Would remove Power Platform's fragility (deprecated triggers, hard-coded IDs) entirely | Contradicts D-01/D-04: existing logic already works, CDO staff can't maintain custom infrastructure after handover, and the brief never asked for it | PRD §5 Non-Goals |
| Standing up a formal Power Platform dev/test environment before making any fixes | Would let every fix be tested safely before touching production | No budget/access path identified yet, and the deadline (semester rollover) doesn't leave room to stand one up first; git-tracked backups + batched, reviewed office-laptop sessions is the pragmatic substitute | D-07 |
