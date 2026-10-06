# Methodology & Confidence Levels

> Read this before trusting any "confirmed" claim in this doc set. This project's analysis was built entirely from **static inspection of exported flow packages** — nobody has watched these flows run live, and no live Power Automate run history has been reviewed yet (as of 2026-09-16). That's a real limit, and every claim in `flow_inventory.md`, `issues_backlog.md`, and the issue docs should be read through it.

Last updated: 2026-09-16

---

## Three tiers of confidence — use these labels, don't blur them

### Tier 1 — Structural fact (certain)

Anything read directly out of a flow's exported `Microsoft.Flow/flows/<guid>/definition.json`: which triggers exist, which actions exist, what they're configured with, what `runAfter` branches exist or don't. This file is the flow's actual configuration — the same thing Power Automate Studio itself reads to run it. There is no inference involved in reading it.

Example: *"Zero of the 14 flows have any action configured to run on `Failed`, `Skipped`, or `TimedOut`."* — `grep`-verified directly against the JSON. Not a claim that could be wrong short of a tooling bug.

### Tier 2 — Platform fact (high confidence, externally verified, not tenant-specific)

General Power Automate / SharePoint / Excel Online / Office Scripts behavior, confirmed against Microsoft's own documentation or community sources — but **not** verified against this specific tenant's actual behavior.

Example: *"The Excel Online (Business) `Run script` action's file parameter can't be set dynamically at runtime."* — true of the connector in general, per Microsoft Learn and Power Platform community threads. Not something observed happening in this tenant's flows specifically.

### Tier 3 — Causal hypothesis (plausible, NOT confirmed)

A claim that a Tier-1 or Tier-2 fact *is the actual cause* of a reported real-world symptom. This is reasoning, not observation — however well-evidenced, it has not been checked against an actual failed run's error message, and it should never be described as "confirmed" without that check.

Example: *"The hard-coded drive-item ID is why 'process ID reading Excel doesn't work.'"* This is the most plausible explanation given the structural fact (Tier 1: the ID is hard-coded) and the platform fact (Tier 2: Office Scripts break when the referenced file is replaced) — but it is **one hypothesis among at least two** (see issue 2b: an Excel formatting mismatch could produce a similar-sounding symptom). Only an actual error message from a failed run, or a reproduction, resolves which one is right.

---

## What would move a Tier 3 hypothesis to confirmed

In order of how easy they are to get, from a personal (non-admin) account first:

1. **Run history.** Power Automate keeps a history of every run, success and failure, usually viewable by anyone with at least read access to the flow — not necessarily edit/owner rights. An actual failed run's error message is the single fastest way to confirm or kill a Tier 3 hypothesis. Check this before assuming an office-laptop visit is required.
2. **Reproduction.** Deliberately triggering the suspected failure condition (e.g., intentionally pointing at a stale file reference) and watching it fail the same way. Requires enough access to run the flow in test mode — may or may not need edit rights depending on the flow's sharing settings.
3. **Live editing + fix + observed success.** The final confirmation — requires the office admin laptop per the project's access constraints.

## Where this project currently stands

- **All 14 flows' structure is Tier 1-confirmed** — see `guides/flow_inventory.md`.
- **The deprecated-trigger replacement and Run Script limitation are Tier 2** — see `changelog/CHANGELOG.md`'s 2026-09-16 research entry.
- **Every specific "this is why X breaks" claim in `guides/issues_backlog.md` and the `refdocs/issues/` docs is Tier 3 until marked otherwise.** Treat the word "confirmed" in those docs as shorthand for "confirmed at the tier stated in context," not as "confirmed to be the real-world cause" — check the specific claim's tier before relying on it for a decision that's expensive to reverse.

## Rule going forward

When writing or updating any analysis in this project: state which tier a claim belongs to, especially when using the word "confirmed." A Tier 1 fact and a Tier 3 hypothesis should never be presented with the same confidence, even when they're in the same sentence.
