"""Flow #14 — Store Student List into SharePoint List.

Findings: refdocs/issues/2026-09-30-flow-14-store-student-list.md

Two fixes, both reusing designs proven on other flows:
  1. Replace the deprecated trigger (as flow 2). This flow never reads the file *content* from the trigger — only its
     path — so no Get file content is needed. BUT the flow archives the processed file into
     `StudentList_DropFile/Archive Student List`, a SUBFOLDER of the folder it watches. The old trigger ignored
     subfolders; the replacement watches them, so without the 'direct child only' guard the flow would re-trigger on
     its own archived file. The guard is therefore mandatory here, not optional.
  2. Try/Catch + Terminate (as flow 3): the flow currently has NO failure alert (a failure just stops).

The Excel `file` parameter is remapped from the old path header to the trigger's {Identifier}. That's the documented
identifier for file actions, but it can't be exercised in the sandbox without a live Excel connection — see the issue doc.
"""
import json

from fixes.f02_acknowledgement_letter import new_trigger
from fixes.f03_add_hc_supervisor import DETAIL_HTML, ERR_EXPR, STEP_EXPR  # noqa: F401  (shared failure-detail pattern)

SOURCE_ZIP = "flows/[LIVE-CDO] UTPCSDCDO Store Student List into SharePoint List.zip"
DISPLAY_NAME = "UTP/CSD/CDO Store Student List into SharePoint List"

SITE = "https://utpmy.sharepoint.com/sites/CareerDevelopmentOfficeCDO"
DOCS_LIBRARY = "3db2d009-d5dd-4ef0-bb47-ee85e8072a7d"
DROP_FOLDER = "/Shared Documents/Power Automate Documents/[UTP_CSD_CDO_AppointmentLetter]/StudentList_DropFile"
LEAF = "StudentList_DropFile"
STUDENT_LIST = "29bdab8e-f4e8-4caf-8e9b-e1437e74f2f5"

OLD_TRIGGER = "When_a_file_is_created_in_a_folder_(deprecated)"
TRY = "Try_-_Store_student_list"
CATCH = "Catch_-_Alert_CDO_staff"
F_LOOP = "Filter_array_-_Failed_in_loop"
F_TOP = "Filter_array_-_Failed_at_top_level"
LOOP = "Apply_to_each_3"
INNER = ["Get_items", "Apply_to_each", "List_rows_present_in_a_table_2", LOOP]
DONE1, DONE2 = "Post_message_in_a_chat_or_channel_13", "Post_message_in_a_chat_or_channel_3"
FAIL1, FAIL2 = "Post_message_FAILED_1", "Post_message_FAILED_2"

PATH_HDR = "triggerOutputs()?['headers/x-ms-file-path-encoded']"
NAME_HDR = "triggerOutputs()?['headers/x-ms-file-name-encoded']"


def _failed_variant(post):
    """Clone a COMPLETED post into a FAILED post, keeping the flow's own wording/colours."""
    f = json.loads(json.dumps(post))
    body = f["inputs"]["parameters"]["body/messageBody"]
    assert "COMPLETED" in body
    body = body.replace("COMPLETED", "FAILED").replace("rgb(97,189,109)", "rgb(184,49,47)")
    f["inputs"]["parameters"]["body/messageBody"] = body.replace("</p>", DETAIL_HTML + "</p>", 1)
    f["metadata"] = {}
    return f


def apply(pkg):
    d = pkg.definition
    defn = d["properties"]["definition"]
    acts = defn["actions"]
    assert OLD_TRIGGER in defn["triggers"], "flow 14 no longer has the deprecated trigger — already fixed?"
    assert TRY not in acts

    # 1. trigger swap + expression remaps (text-level: the header expressions appear in params and, in the sandbox, a Compose)
    defn["triggers"] = new_trigger(SITE, DOCS_LIBRARY, DROP_FOLDER, LEAF)
    text = json.dumps(defn)
    text = text.replace(PATH_HDR, "triggerOutputs()?['body/{Identifier}']").replace(NAME_HDR, "triggerOutputs()?['body/{FilenameWithExtension}']")
    defn = json.loads(text)
    d["properties"]["definition"] = defn
    acts = defn["actions"]

    # 2. Try/Catch
    inner = {n: acts.pop(n) for n in INNER}
    inner["Get_items"]["runAfter"] = {}
    acts[TRY] = {"type": "Scope", "runAfter": {"Initialize_variable": ["Succeeded"]}, "actions": inner}
    for n in (DONE1, DONE2):
        acts[n]["runAfter"] = {TRY: ["Succeeded"]}

    fail1, fail2 = _failed_variant(acts[DONE1]), _failed_variant(acts[DONE2])
    fail1["runAfter"] = {F_TOP: ["Succeeded"]}
    fail2["runAfter"] = {FAIL1: ["Succeeded", "Failed"]}

    def flt(src, after):
        return {"type": "Query", "runAfter": after, "inputs": {"from": f"@result('{src}')", "where": "@equals(item()?['status'], 'Failed')"}}

    acts[CATCH] = {
        "type": "Scope",
        "runAfter": {TRY: ["Failed", "TimedOut"]},
        "actions": {F_LOOP: flt(LOOP, {}), F_TOP: flt(TRY, {F_LOOP: ["Succeeded"]}), FAIL1: fail1, FAIL2: fail2},
    }
    acts["Terminate_-_Mark_run_as_failed"] = {
        "type": "Terminate",
        "runAfter": {CATCH: ["Succeeded", "Failed", "TimedOut"]},
        "inputs": {"runStatus": "Failed", "runError": {"code": "StoreStudentListFailed",
                   "message": "Store Student List failed at: @{" + STEP_EXPR + "}"}},
    }
    pkg.definition = d
    left = [w for w in ("headers/x-ms-file",) if w in json.dumps(pkg.definition)]
    if left:
        raise SystemExit(f"flow 14 fix left old trigger references: {left}")


def sandboxify(pkg, cfg):
    """Sandbox conversion: Excel read -> Compose of sample rows chosen by the dropped file's name; watch the sandbox folder."""
    site = cfg["replace"][SITE]
    d = pkg.definition
    defn = d["properties"]["definition"]
    trig = defn["triggers"][OLD_TRIGGER]
    enc = "%252fDocuments%252fCDO-Sandbox%252fStudentList_DropFile"
    trig["inputs"]["parameters"]["folderId"] = enc
    trig["metadata"] = {"operationMetadataId": trig.get("metadata", {}).get("operationMetadataId", "00000000-0000-0000-0000-000000000000")}

    def row(n, **kw):
        base = {"Year": "2026", "Course ": "Test Course", "Semester": "1", "Batch": "B1", "Intake": "Sep", "Student ID": f"T{n:04d}",
                "Student Name": f"Test Student {n}", "Gender": "F", "Nationality": "Test", "Country": "Test", "Student Program": "TP",
                "CGPA": "3.5", "Sponsor": "Self", "Email Address": f"Test.Student.{n}@example.test"}
        base.update(kw)
        return base

    good = [row(1), row(2)]
    bad = [row(1), row(2, **{"Student ID": "X" * 300})]
    q = lambda rows: json.dumps({"body/value": rows}).replace("'", "''")
    fname = f"toLower({NAME_HDR.replace('triggerOutputs()', 'triggerOutputs()')})"
    sample = (
        f"@if(contains({fname}, 'readfail'), div(1, 0), "
        f"json(if(contains({fname}, 'rowfail'), '{q(bad)}', '{q(good)}')))"
    )
    real = cfg.get("_realexcel")
    if real:
        # REAL Excel read of the dropped workbook (sandbox OneDrive, table StudentList). The `file` parameter is left exactly as the
        # flow has it: the old path header in the baseline, the trigger's {Identifier} once apply() has remapped it (fixed).
        from fixes.f12_hc_supervisor_masterlist_checking import _strip_file_hints
        lr = defn["actions"]["List_rows_present_in_a_table_2"]
        _strip_file_hints(lr)
        lr["inputs"]["parameters"].update({"source": "me", "drive": "me", "table": "StudentList"})
    else:
        defn["actions"]["List_rows_present_in_a_table_2"] = {
            "type": "Compose", "runAfter": defn["actions"]["List_rows_present_in_a_table_2"]["runAfter"], "inputs": sample}
    # the sandbox Student List's built-in Title is required by the connector schema (production's isn't)
    defn["actions"][LOOP]["actions"]["Condition"]["actions"]["Create_item_2"]["inputs"]["parameters"]["item/Title"] = "sandbox"
    pkg.definition = d
    if not real:
        pkg.remove_connector("shared_excelonlinebusiness")


# ---- real-Excel scenarios: tools/sandbox/pw.py stage 14 ok (once), import 14 baselinex|fixedx, run 14 ok|readfail baselinex|fixedx
WATCH = "/Documents/CDO-Sandbox/StudentList_DropFile"
ARCHIVE = WATCH + "/Archive Student List"
SL = "CDO Sandbox - Student List"
_BOTH = ("baselinex", "fixedx")
SCENARIOS = {
    # 8 rows: 1,2,4,5,6 are new; 3 repeats row 2's email and 7 is row 1's email in other case/spacing (both must be skipped);
    # 8 has no email address (created once: the flow only compares what it has)
    "ok": {"clear": [SL], "clearFolders": [WATCH], "timeout": 900, "count": ["Create_item_2"], "countLists": [SL],
           "inspect": [WATCH, ARCHIVE], "upload": [{"folder": "/Documents/CDO-Sandbox/F14", "file": "StudentList_TEST.xlsx"}],
           "drop": [{"folder": WATCH, "file": "StudentList_TEST.xlsx", "name": "StudentList_{pkg}_ok.xlsx"}],
           "expect": {p: {"status": "Succeeded", "after": {SL: 6}} for p in _BOTH}},
    "readfail": {"clear": [SL], "clearFolders": [WATCH], "timeout": 1500, "count": ["Create_item_2"], "countLists": [SL],
                 "inspect": [WATCH, ARCHIVE], "upload": [],
                 # a valid workbook without a table called StudentList (a corrupt file made the Excel connector retry for 26 minutes)
                 "drop": [{"folder": WATCH, "file": "StudentList_wrongtable.xlsx", "name": "StudentList_{pkg}_wrongtable.xlsx"}],
                 "expect": {"baselinex": {"status": "Failed", "failedAction": "List_rows_present_in_a_table_2", "after": {SL: 0}},
                            "fixedx": {"status": "Failed", "failedAction": "List_rows_present_in_a_table_2", "after": {SL: 0}}}},
}
