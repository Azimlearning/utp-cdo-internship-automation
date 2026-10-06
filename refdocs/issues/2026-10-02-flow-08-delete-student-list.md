# Flow 8: Delete Student List from SharePoint List

> Sandbox workflow (D-08). Fix module: `tools/fixes/f08_delete_student_list.py`, using the shared `tools/fixes/trycatch.py`.

## Status

🔶 **Sandbox-tested with a REAL failure (no stubbing); one check left for you (Teams alert wording).** 2026-10-02. This is the cleanest test so far: the only change in the sandbox copy is the trigger and, for the `deletefail` scenario, one delete aimed at a non-existent item id, which makes SharePoint return a genuine "Item Not Found".

## What it does

PowerApp button → RUNNING ×2 → reads the Student List (capped at 10,000 items) → deletes every item → COMPLETED ×2; FAILED ×2 hangs off the COMPLETED posts.

## Findings

| # | Finding | Evidence | Fix status |
|---|---|---|---|
| 8.1 | **A failed run reports "Succeeded".** Real SharePoint failure (Item Not Found): the loop failed, COMPLETED was skipped, the generic FAILED messages fired, and the header read "Your flow ran successfully" | **Observed** | ✅ Try/Catch + Terminate |
| 8.2 | A failed run leaves the Student List partly deleted/untouched with no report of which items | Read | 🔶 the alert now names the failing action and its error (e.g. "Delete_item failed: Item Not Found") |
| 8.3 | FAILED message has no step, error or link | Read | ✅ |
| 8.4 | The read is capped at 10,000 items; a list larger than that would be only partly deleted | Read | ➖ low risk (a semester's student list is far smaller); noted |
| 8.5 | No confirmation before deleting the whole list | Read | ⬜ PowerApp suggestion (see MANUAL-TODO B) |

## Test results (sandbox)

| Case | Package | Result |
|---|---|---|
| deletefail (3 students; each delete targets a missing id) | baseline | list stays 3; run **Succeeded**; generic FAILED posts sent. Evidence `evidence/flow-08/01-…` |
| deletefail | fixed | Try failed on `Delete_item` ("Item Not Found") → **Catch ✓ (4 actions)** → **Terminate ✓** → run **Failed**; banner names the action and error. Evidence `evidence/flow-08/02-…` |
| ok | fixed | list **3 → 0**, run **Succeeded** |

**Not confirmed:** Teams alert wording.

## Office steps

1. Back up flow 8 into `flows/` and commit.
2. Wrap `Get items` + `Apply to each` in `Try - Delete student list`; Catch/Terminate as in flow 3. Or import `build/prod/flow08-prod.zip` with **Update**.
3. Test on a **copy** of the Student List first.
