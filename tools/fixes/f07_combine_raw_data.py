"""Flow #7: Combine raw data.

Copies the FinalizedHeader template into a RawData workbook, then for every student looks up their registrations and adds rows
to the workbook (Excel 'Add a row' x6 in nested loops), waits 30 s, runs an Office Script, emails the PIC, posts COMPLETED x2,
and finally duplicates the file into MasterList_RawData_ToBeProcess. FAILED x2 only hangs off that final duplicate step.

Fix (fixes/trycatch.py):
  * Try/Catch + Terminate around everything including the final duplicate copy. The COMPLETED posts now fire only after the
    duplicate succeeds (before: COMPLETED was posted first, then the copy ran).
  * The per-student loop runs ONE iteration at a time (concurrency 1). Default parallelism lets up to 20 iterations write rows
    into the same workbook at once, a classic cause of lost rows / file-locked errors. NOT provable in the sandbox (Excel is
    stubbed) - flagged untested in the issue doc.
Sandbox: Excel add-row, the Office Script and the template read are stubbed; files are created in the sandbox library.
"""
import json

from fixes import trycatch as tc

SOURCE_ZIP = "flows/[LIVE-CDO] UTPCSDCDO Combine raw data.zip"
DISPLAY_NAME = "UTP/CSD/CDO Combine raw data"
SITE = "https://utpmy.sharepoint.com/sites/CareerDevelopmentOfficeCDO"
TRY = "Try_-_Combine_raw_data"
SCRIPT = "Run_script"
INNER = ["Scope_-_Create_new_folder_and_files", "Get_file_properties", "Get_items_2", "Apply_to_each_3", "Delay", SCRIPT,
         "Get_file_content_using_path_2", "Send_an_email_(V2)", "Create_file_-_Duplicated_File"]
STUDENTS = "CDO Sandbox - Student List"
REGISTERED = "CDO Sandbox - Report Duty Registration"
_ST = {"StudentName": "Combine Student A", "EmailAddress": "combine.a@sandbox.test"}
_RG = {"field_2": "Combine Student A", "field_5": "combine.a@sandbox.test"}
# tools/sandbox/pw.py run 07 <name> baseline|fixed
SCENARIOS = {
    "scriptfail": {"clear": [STUDENTS, REGISTERED], "seed": {STUDENTS: [_ST], REGISTERED: [_RG]}, "trigger": "scriptfail",
                   "expect": {"baseline": {"status": "Succeeded"}, "fixed": {"status": "Failed", "failedAction": "Run_script"}}},
    "ok": {"clear": [STUDENTS, REGISTERED], "seed": {STUDENTS: [_ST], REGISTERED: [_RG]}, "trigger": "ok",
           "expect": {"baseline": {"status": "Succeeded"}, "fixed": {"status": "Succeeded"}}},
}
ADD_ROWS = ["Add_a_row_into_a_table", "Add_a_row_into_a_table_2", "Add_a_row_into_a_table_3", "Add_a_row_into_a_table_4"]


def apply(pkg):
    d = pkg.definition
    defn = d["properties"]["definition"]
    a = defn["actions"]
    # the duplicate copy becomes part of the work: it follows the email directly; COMPLETED posts move to after Try
    a["Create_file_-_Duplicated_File"]["runAfter"] = {"Send_an_email_(V2)": ["Succeeded"]}
    a["Apply_to_each_3"].setdefault("runtimeConfiguration", {})["concurrency"] = {"repetitions": 1}
    tc.wrap(defn, inner=INNER, try_name=TRY,
            fail_posts=["Post_message_in_a_chat_or_channel_5", "Post_message_in_a_chat_or_channel_4"],
            loops=["Apply_to_each_3"], code="CombineRawDataFailed", label="Combine raw data")
    pkg.definition = d


def _stub_add_rows(actions):
    for k, v in list(actions.items()):
        if v["type"] == "OpenApiConnection" and v["inputs"]["host"].get("operationId") == "AddRowV2":
            actions[k] = {"type": "Compose", "runAfter": v.get("runAfter", {}), "inputs": v["inputs"]["parameters"]["item"]}
        _stub_add_rows(v.get("actions", {}))
        if v.get("else"):
            _stub_add_rows(v["else"].get("actions", {}))


def sandboxify(pkg, cfg):
    d = pkg.definition
    defn = d["properties"]["definition"]
    defn["triggers"] = tc.list_item_trigger(cfg["replace"][SITE], cfg["harness"]["run_trigger_list"])
    a = defn["actions"]
    scope = a["Scope_-_Create_new_folder_and_files"]["actions"]
    scope["Get_file_content_using_path"] = {"type": "Compose", "runAfter": {}, "inputs": "stub template workbook"}
    _stub_add_rows(a)
    a[SCRIPT] = {"type": "Compose", "runAfter": a[SCRIPT]["runAfter"],
                 "inputs": "@if(equals(triggerBody()?['Title'], 'scriptfail'), div(1, 0), 'script stub ok')"}
    a["Delay"]["inputs"]["interval"] = {"count": 1, "unit": "Second"}
    pkg.definition = d
    pkg.remove_connector("shared_excelonlinebusiness_1")
