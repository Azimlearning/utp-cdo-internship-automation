"""Flow #8: Delete Student List from SharePoint List.

Reads every Student List item (pagination cap 10,000) and deletes each; COMPLETED x2, FAILED x2 off the COMPLETED posts.
Same shape as flows 3/4/6 -> shared Try/Catch + Terminate (fixes/trycatch.py).

Sandbox: list-item trigger; scenario 'deletefail' makes the delete target a non-existent item id, producing a REAL SharePoint
failure (no stubbing needed).
"""
from fixes import trycatch as tc

SOURCE_ZIP = "flows/[LIVE-CDO] UTPCSDCDO Delete Student List from SharePoint List.zip"
DISPLAY_NAME = "UTP/CSD/CDO Delete Student List"
SITE = "https://utpmy.sharepoint.com/sites/CareerDevelopmentOfficeCDO"
TRY = "Try_-_Delete_student_list"


def apply(pkg):
    d = pkg.definition
    tc.wrap(d["properties"]["definition"], inner=["Get_items", "Apply_to_each"], try_name=TRY,
            fail_posts=["Post_message_in_a_chat_or_channel_4", "Post_message_in_a_chat_or_channel_5"],
            loops=["Apply_to_each"], code="DeleteStudentListFailed", label="Delete Student List")
    pkg.definition = d


def sandboxify(pkg, cfg):
    d = pkg.definition
    defn = d["properties"]["definition"]
    defn["triggers"] = tc.list_item_trigger(cfg["replace"][SITE], cfg["harness"]["run_trigger_list"])
    p = defn["actions"]["Apply_to_each"]["actions"]["Delete_item"]["inputs"]["parameters"]
    p["id"] = "@if(equals(triggerBody()?['Title'], 'deletefail'), 999999, items('Apply_to_each')?['ID'])"
    pkg.definition = d
