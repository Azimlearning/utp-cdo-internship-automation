"""Flow #6: Clear Raw Database.

Deletes EVERY item in the Report Duty Registration list, then resets the Excel SummaryTable with an Office Script; COMPLETED x2
after the script, FAILED x2 hanging off the COMPLETED posts (same pattern as flows 3/4/5).

Fix: Try/Catch + Terminate via fixes/trycatch.py. Sandbox: list-item trigger, the Office Script is stubbed (scenario 'scriptfail'
fails it after the deletes, giving the half-cleared state the real flow can produce).
"""
from fixes import trycatch as tc

SOURCE_ZIP = "flows/[LIVE-CDO] UTPCSDCDO Clear Raw Database.zip"
DISPLAY_NAME = "UTP/CSD/CDO Clear Raw Database"
SITE = "https://utpmy.sharepoint.com/sites/CareerDevelopmentOfficeCDO"
SCRIPT = "Run_script_-_Reset_Summary_Table"
TRY = "Try_-_Clear_database"


def apply(pkg):
    d = pkg.definition
    tc.wrap(d["properties"]["definition"], inner=["Get_items", "Apply_to_each", SCRIPT], try_name=TRY,
            fail_posts=["Post_message_in_a_chat_or_channel_4", "Post_message_in_a_chat_or_channel_5"],
            loops=["Apply_to_each"], code="ClearRawDatabaseFailed", label="Clear Raw Database")
    pkg.definition = d


def sandboxify(pkg, cfg):
    d = pkg.definition
    defn = d["properties"]["definition"]
    defn["triggers"] = tc.list_item_trigger(cfg["replace"][SITE], cfg["harness"]["run_trigger_list"])
    a = defn["actions"]
    a[SCRIPT] = {"type": "Compose", "runAfter": a[SCRIPT]["runAfter"],
                 "inputs": "@if(equals(triggerBody()?['Title'], 'scriptfail'), div(1, 0), 'script stub ok')"}
    pkg.definition = d
    pkg.remove_connector("shared_excelonlinebusiness_1")
