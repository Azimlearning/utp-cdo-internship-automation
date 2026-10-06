"""Flow #5: Bulk Email To Start Registration for Current Semester Internship Student.

Sends batched BCC emails (max recipients per email from the config item) to every student in the Student List, with the
report-duty guideline attachments and links. FAILED x2 hangs off the last COMPLETED post (same pattern as flows 3/4).

Fix: Try/Catch + Terminate (fixes/trycatch.py). Variable initialisations must stay top-level, so the logo file read is moved
into the Try scope (imageStr is initialised empty and filled by a Set variable inside Try).

Sandbox: EVERY recipient is redirected to the tester's own address; attachments/links scopes and the template image are
stubbed; scenarios come from the Flow Run Trigger list item title (ok / sendfail). Never send from a sandbox to real students.
"""
import json

from fixes import trycatch as tc

SOURCE_ZIP = "flows/[LIVE-CDO] UTPCSDCDO Bulk Email To Start Registration for Current Semester Internship Student.zip"
DISPLAY_NAME = "UTP/CSD/CDO Bulk Email To Start Registration"
SITE = "https://utpmy.sharepoint.com/sites/CareerDevelopmentOfficeCDO"
TRY = "Try_-_Send_bulk_emails"
SCOPES = ["Scope_-_Get_Guideline_Attachment", "Scope_-_Get_Other_Files_Attachment", "Scope_-Get_Link_Name_and_Link_URL"]
SANDBOX_TO = "fakhrul_22012087@utp.edu.my"

STUDENTS = "CDO Sandbox - Student List"
_S = [{"StudentName": f"Bulk Student {c}", "EmailAddress": f"bulk.{c.lower()}@sandbox.test"} for c in "ABC"]
SENDS = ["Send_an_email_(V2)", "Send_an_email_(V2)_2"]
# tools/sandbox/pw.py run 05 <name> baseline|fixed   (3 students, max recipients per email comes from the config item)
SCENARIOS = {
    "ok": {"clear": [STUDENTS], "seed": {STUDENTS: _S}, "trigger": "ok", "count": SENDS,
           "expect": {"baseline": {"status": "Succeeded"}, "fixed": {"status": "Succeeded"}}},
    "sendfail": {"clear": [STUDENTS], "seed": {STUDENTS: _S}, "trigger": "sendfail", "count": SENDS,
                 "expect": {"baseline": {"status": "Succeeded"}, "fixed": {"status": "Failed"}}},
}


def apply(pkg):
    d = pkg.definition
    defn = d["properties"]["definition"]
    a = defn["actions"]
    # move the logo read into Try: init the variable empty, fill it inside Try
    img = a["Initialize_variable"]["inputs"]["variables"][0]["value"]  # original (or sandbox-stubbed) expression
    a["Initialize_variable"]["inputs"]["variables"][0]["value"] = ""
    a["Initialize_variable"]["runAfter"] = {"Post_message_in_a_chat_or_channel_2": ["Succeeded"]}
    a["Get_file_content"]["runAfter"] = {"Initialize_variable_7": ["Succeeded"]}
    a["Set_variable_-_imageStr"] = {"type": "SetVariable", "runAfter": {"Get_file_content": ["Succeeded"]},
                                    "inputs": {"name": "imageStr", "value": img}}
    first = next((s for s in SCOPES if s in a), "Get_items")
    a[first]["runAfter"] = {"Set_variable_-_imageStr": ["Succeeded"]}
    if first == "Get_items":
        pass
    tc.wrap(defn, inner=["Get_file_content", "Set_variable_-_imageStr", *SCOPES, "Get_items", "Apply_to_each"], try_name=TRY,
            fail_posts=["Post_message_in_a_chat_or_channel_4", "Post_message_in_a_chat_or_channel_5"],
            loops=["Apply_to_each"], code="BulkEmailFailed", label="Bulk email")
    pkg.definition = d


def sandboxify(pkg, cfg):
    site = cfg["replace"][SITE]
    d = pkg.definition
    defn = d["properties"]["definition"]
    a = defn["actions"]
    defn["triggers"] = tc.list_item_trigger(site, cfg["harness"]["run_trigger_list"])
    # stub the logo file: a plain Compose (its body() has no '$content'), and a literal image string for the variable
    a["Get_file_content"] = {"type": "Compose", "runAfter": a["Get_file_content"]["runAfter"], "inputs": "stub"}
    a["Initialize_variable"]["inputs"]["variables"][0]["value"] = "<img src=\"data:image/png;base64,iVBORw0KGgo=\" width=\"100\" height=\"90\"/>"
    for s in SCOPES:
        a.pop(s, None)
    a["Get_items"]["runAfter"] = {"Initialize_variable_7": ["Succeeded"]}
    loop = a["Apply_to_each"]["actions"]
    loop["Append_to_array_variable_3"]["inputs"]["value"] = SANDBOX_TO
    to = "@if(equals(triggerBody()?['Title'], 'sendfail'), 'not-an-email', '" + SANDBOX_TO + "')"
    for path in (loop["Condition"]["actions"]["Send_an_email_(V2)"], loop["Condition_2"]["actions"]["Send_an_email_(V2)_2"]):
        path["inputs"]["parameters"]["emailMessage/To"] = to
    pkg.definition = d
