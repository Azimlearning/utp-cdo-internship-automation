"""Flow #10: Email for Report Duty Reminder.

PowerApp button -> RUNNING x2 -> reads the Student List and the Report Duty Registration list -> for each student whose email is
NOT among the registered emails, sends a reminder (Outlook), counting sends -> COMPLETED x2; FAILED x2 off the COMPLETED posts.
A send that fails (e.g. a malformed address on the Student List) fails one loop iteration, the other students are still emailed,
COMPLETED is skipped and the generic FAILED posts fire -> run reported "Succeeded".

Fix: Try/Catch + Terminate (fixes/trycatch.py).
Sandbox: list-item trigger; EVERY reminder goes to the tester's own address (subject is tagged with the student's real address so
sends can be counted); a student whose address contains no '@' keeps that address and so fails for real.
"""
from fixes import trycatch as tc

SOURCE_ZIP = "flows/[LIVE-CDO] UTPCSDCDO Email for Report Duty Reminder.zip"
DISPLAY_NAME = "UTP/CSD/CDO Email for Report Duty Reminder"
SITE = "https://utpmy.sharepoint.com/sites/CareerDevelopmentOfficeCDO"
TRY = "Try_-_Send_reminders"
ME = "fakhrul_22012087@utp.edu.my"
SEND = "Send_an_email_(V2)"

STUDENTS = "CDO Sandbox - Student List"
REGISTERED = "CDO Sandbox - Report Duty Registration"
_A = {"StudentName": "Student A Registered", "EmailAddress": "a.registered@sandbox.test"}
_B = {"StudentName": "Student B Pending", "EmailAddress": "b.pending@sandbox.test"}
_C = {"StudentName": "Student C BadAddress", "EmailAddress": "not-an-email"}
_D = {"StudentName": "Student D DupOfB", "EmailAddress": "b.pending@sandbox.test"}
_SEED = {REGISTERED: [{"field_2": _A["StudentName"], "field_5": _A["EmailAddress"]}]}
# tools/sandbox/pw.py run 10 <name> baseline|fixed
SCENARIOS = {
    "badaddr": {  # one malformed address + one duplicate student among valid ones
        "clear": [STUDENTS, REGISTERED], "seed": {**_SEED, STUDENTS: [_A, _B, _C, _D]}, "count": [SEND],
        "expect": {"baseline": {"status": "Succeeded", "counts": {SEND: {"Succeeded": 2, "Failed": 1}}},
                   "fixed": {"status": "Failed", "failedAction": SEND, "counts": {SEND: {"Succeeded": 2, "Failed": 1}}}}},
    # the first list read fails before the loop runs: the Catch must still alert although its nested-condition filter
    # points at a Condition that never executed
    "readfail": {
        "clear": [STUDENTS, REGISTERED], "seed": {**_SEED, STUDENTS: [_A, _B]}, "trigger": "readfail", "count": [SEND],
        "expect": {"fixed": {"status": "Failed", "failedAction": "Get_items", "counts": {SEND: {"Succeeded": 0}}}}},
    "ok": {
        "clear": [STUDENTS, REGISTERED], "seed": {**_SEED, STUDENTS: [_A, _B]}, "count": [SEND],
        "expect": {"baseline": {"status": "Succeeded", "counts": {SEND: {"Succeeded": 1}}},
                   "fixed": {"status": "Succeeded", "counts": {SEND: {"Succeeded": 1}}},
                   # the probe fails first inside the Try scope: no reminder may be sent
                   "fixedprobe": {"status": "Failed", "failedAction": "Probe_-_Force_a_failure_(DELETE_AFTER_TEST)",
                                  "counts": {SEND: {"Succeeded": 0, "Failed": 0}}}}},
}


def apply(pkg):
    d = pkg.definition
    tc.wrap(d["properties"]["definition"], inner=["Get_items", "Get_items_2", "Apply_to_each_3", "Apply_to_each"], try_name=TRY,
            fail_posts=["Post_message_in_a_chat_or_channel_4", "Post_message_in_a_chat_or_channel_5"],
            loops=["Apply_to_each"], code="ReportDutyReminderFailed", label="Report Duty Reminder")
    pkg.definition = d


def sandboxify(pkg, cfg):
    d = pkg.definition
    defn = d["properties"]["definition"]
    defn["triggers"] = tc.list_item_trigger(cfg["replace"][SITE], cfg["harness"]["run_trigger_list"])
    # the send action sits inside Apply_to_each > Condition in the baseline; apply() has not moved it yet at this point or has
    # moved it into the Try scope, so look for it in both places
    acts = defn["actions"]
    loop = acts["Apply_to_each"] if "Apply_to_each" in acts else acts[TRY]["actions"]["Apply_to_each"]
    p = loop["actions"]["Condition"]["actions"][SEND]["inputs"]["parameters"]
    addr = "toLower(trim(items('Apply_to_each')?['EmailAddress']))"
    p["emailMessage/To"] = f"@if(contains({addr}, '@'), '{ME}', {addr})"
    p["emailMessage/Cc"] = ME
    p["emailMessage/Subject"] = "@{concat('[SANDBOX reminder for ', " + addr + ", '] ', 'Reminder')}"
    # scenario 'readfail': an invalid OData filter makes SharePoint reject the Student List read (a real failure, pre-loop)
    acts["Get_items"]["inputs"]["parameters"]["$filter"] = "@if(equals(triggerBody()?['Title'], 'readfail'), 'NoSuchColumn eq 1', 'ID gt 0')"
    pkg.definition = d
