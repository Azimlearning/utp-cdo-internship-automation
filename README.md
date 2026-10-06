# UTP CDO Internship Automation

Stabilizing and migrating UTP's Career Development Office (CDO) internship system — a PowerApp + 14 Power Automate flows + SharePoint/Excel — off a departing staff member's account and off its two confirmed root causes of "it randomly stops working."

**Status:** P0 (docs) done · P1 (design) in progress · P2–P6 not started — see [`refdocs/STATUS.md`](refdocs/STATUS.md)

## What it does

Each semester, students fill in internship details in a PowerApp (previous data auto-fills, but is editable). On submit, data lands in a SharePoint list. The system checks host companies/supervisors against an Excel master list and buckets each into new / exact-match / partial-match, so CDO staff only manually review the new and partial ones instead of every record. Once reviewed and confirmed, a button sends a personalized appointment/acknowledgement letter (PDF) to each host company supervisor. Separate buttons send the initial report-duty registration email to all students and a reminder to anyone who hasn't responded. Every automated process is meant to post running/processing/success (and, after this project's fixes, failure) notifications to Teams. At semester end, the current data is cleared and the master-list templates are reset in place for the next intake.

Full breakdown of all 14 flows, their triggers, and confirmed issues: [`refdocs/guides/flow_inventory.md`](refdocs/guides/flow_inventory.md).

## Requirements

- Access to the UTP Microsoft 365 tenant (SharePoint, Excel Online, Outlook, Teams, Power Automate, Power Apps)
- For any live change: the office admin laptop (see [`CLAUDE.md`](CLAUDE.md) hard constraints) — a personal account can read/analyze/plan but not make a live edit stick
- `unzip` (or Power Automate Studio's own export/import) to inspect or update a flow package

## Setup

There's no install step — this repo is documentation plus the 14 flow export packages, not a runnable codebase.

```bash
git clone <this repo>
# to inspect a flow's current definition:
unzip -o -q "flows/<flow name>.zip" -d <scratch-dir>
cat "<scratch-dir>/Microsoft.Flow/flows/<guid>/definition.json"
```

## Environment

No `.env` — every integration authenticates via Microsoft OAuth connections configured inside Power Automate Studio, not files in this repo. Site URLs, folder paths, and the handful of hard-coded IDs this project's fixes revolve around are documented in [`refdocs/guides/env_setup.md`](refdocs/guides/env_setup.md).

## Usage

```bash
# Inspect what changed in the live flows since the repo's snapshot
git log --follow -- flows/
```

Actual "usage" of the system itself happens inside the PowerApp and Power Automate — this repo is where the plan, history, and rollback copies live.

## Project layout

```
CDO - Internship powerapps automation/
├── CLAUDE.md                 ← operating brief for AI sessions
├── README.md                 ← this file
├── flows/                    ← the 14 Power Automate flow export .zip files (canonical, re-importable)
├── .claude/
│   ├── settings.json
│   ├── memory/preflight.md   ← six-question session-start gate
│   ├── agents/                ← doc-keeper, codebase-explorer, feature-planner
│   └── commands/              ← /session-end, /plan-feature, /status
└── refdocs/
    ├── cdo-internship-automation-PRD.md
    ├── STATUS.md              ← read this first
    ├── cdo-internship-automation-sources.md
    ├── context-2026-09-16-brief.md   ← raw founding brief
    ├── guides/
    │   ├── flow_inventory.md  ← every flow's trigger/connectors/purpose/issues
    │   ├── env_setup.md       ← site URLs, folder paths, hard-coded IDs
    │   ├── checklist.md       ← pre-change checklist for live edits
    │   └── issues_backlog.md  ← the full tracked issue list — work one at a time
    ├── issues/                 ← per-issue analysis/review/fix, one file per backlog item in progress
    ├── changelog/
    │   ├── CHANGELOG.md
    │   └── DECISIONS.md
    ├── plans/                 ← what & why, one file per phase
    └── execution/             ← how & in what order, one file per phase
```

## Documentation

| Doc | What's in it |
|---|---|
| [`refdocs/STATUS.md`](refdocs/STATUS.md) | Where the fix effort actually is right now |
| [`refdocs/cdo-internship-automation-PRD.md`](refdocs/cdo-internship-automation-PRD.md) | Scope, architecture, roadmap, decision log |
| [`refdocs/guides/methodology.md`](refdocs/guides/methodology.md) | The confidence-tier system every "confirmed" claim in this project should be read through — read this first |
| [`refdocs/guides/flow_inventory.md`](refdocs/guides/flow_inventory.md) | Every one of the 14 flows: trigger, connectors, purpose, confirmed issues |
| [`refdocs/guides/issues_backlog.md`](refdocs/guides/issues_backlog.md) | The full tracked issue list — pick one at a time |
| [`refdocs/issues/`](refdocs/issues/) | Per-issue analysis, review, and fix design for whichever backlog item is currently being worked |
| [`refdocs/guides/previous_system_guide_notes.md`](refdocs/guides/previous_system_guide_notes.md) | Notes on the original 2023–2024 admin user guide — what it confirms/resolves |
| [`refdocs/context-2023-2024-admin-user-guide.pdf`](refdocs/context-2023-2024-admin-user-guide.pdf) | The original admin guide itself (source document) |
| [`refdocs/changelog/CHANGELOG.md`](refdocs/changelog/CHANGELOG.md) | Session-by-session history |
| [`refdocs/changelog/DECISIONS.md`](refdocs/changelog/DECISIONS.md) | Why things are the way they are |
| [`refdocs/guides/env_setup.md`](refdocs/guides/env_setup.md) | Site URLs, folder paths, hard-coded IDs this project's fixes revolve around |
| [`refdocs/guides/checklist.md`](refdocs/guides/checklist.md) | Pre-change checklist for editing a live flow |
| [`CLAUDE.md`](CLAUDE.md) | Operating brief for AI sessions on this repo |

Internal UTP CDO project — not licensed for external distribution.
