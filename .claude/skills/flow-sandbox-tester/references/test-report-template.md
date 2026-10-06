# Sandbox test record — template

Paste into the flow's issue doc under `## Sandbox test results`. Lead with the result.

```markdown
## Sandbox test results — YYYY-MM-DD

**Result:** [Baseline reproduced the failure / did not reproduce]. [Fixed package passed N/M cases.]

| Package | Built from | Imported as |
|---|---|---|
| baseline | `flows/<zip>` @ commit `<sha>` | `[SANDBOX-BASELINE] <name>` |
| fixed | same + `tools/fixes/fNN_*.py` | `[SANDBOX-FIXED] <name>` |

| # | Case | Package | Input | Expected | Observed (run status / failed action / message) | Pass? |
|---|---|---|---|---|---|---|
| T1 | ... | baseline | ... | ... | ... | ✅/❌ |

**Evidence:** `evidence/flow-NN/01-...png` — what it proves.

**Notes:** import warnings, connector quirks, anything the office-laptop step must know. Sandbox flow turned off: yes/no.
```

Rules: exact action names and error text; "Pass" only for a case whose run history was actually read; never include real student data.
