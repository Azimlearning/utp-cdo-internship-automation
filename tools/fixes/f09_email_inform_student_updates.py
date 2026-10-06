"""Flow #9: Email To Inform Student Updates.

PowerApp button with five text fields (to, name, message, cc, subject) -> RUNNING x2 -> sends an email to the student ->
Teams message to the same student -> COMPLETED x2; FAILED x2 off the COMPLETED posts. The address is not validated, so a typo in
the PowerApp field fails the send (the flow 1 problem) and the run is reported "Succeeded".

Fix: Try/Catch + Terminate (fixes/trycatch.py) around the email + Teams message.
Sandbox: the PowerApp trigger fields are replaced by fixed test values and the recipient is always the tester's own address;
scenario 'badaddr' sends to 'not-an-email'.
"""
import json

from fixes import trycatch as tc

SOURCE_ZIP = "flows/[LIVE-CDO] UTPCSDCDO Email To Inform Student Updates.zip"
DISPLAY_NAME = "UTP/CSD/CDO Email To Inform Student Updates"
SITE = "https://utpmy.sharepoint.com/sites/CareerDevelopmentOfficeCDO"
TRY = "Try_-_Email_student"
ME = "fakhrul_22012087@utp.edu.my"


SEND = "Send_an_email_(V2)"
PROBE = "Probe_-_Force_a_failure_(DELETE_AFTER_TEST)"
# tools/sandbox/pw.py run 09 <name> baseline|fixed|fixedprobe
SCENARIOS = {
    "badaddr": {"trigger": "badaddr", "count": [SEND],
                "expect": {"baseline": {"status": "Succeeded", "counts": {SEND: {"Failed": 1}}},
                           "fixed": {"status": "Failed", "failedAction": SEND}}},
    "ok": {"trigger": "ok", "count": [SEND],
           "expect": {"baseline": {"status": "Succeeded", "counts": {SEND: {"Succeeded": 1}}},
                      "fixed": {"status": "Succeeded", "counts": {SEND: {"Succeeded": 1}}},
                      # the probe fails first: the real send must never run
                      "fixedprobe": {"status": "Failed", "failedAction": PROBE, "counts": {SEND: {"Succeeded": 0, "Failed": 0}}}}},
}


def apply(pkg):
    d = pkg.definition
    tc.wrap(d["properties"]["definition"], inner=["Send_an_email_(V2)", "Post_message_in_a_chat_or_channel_2"], try_name=TRY,
            fail_posts=["Post_message_in_a_chat_or_channel_5", "Post_message_in_a_chat_or_channel_6"],
            loops=[], code="EmailStudentFailed", label="Email student update")
    pkg.definition = d


def sandboxify(pkg, cfg):
    d = pkg.definition
    defn = d["properties"]["definition"]
    defn["triggers"] = tc.list_item_trigger(cfg["replace"][SITE], cfg["harness"]["run_trigger_list"])
    t = json.dumps(defn["actions"])
    rep = {
        "triggerBody()['text_1']": "'Test Student'",
        "triggerBody()['text_2']": "'Sandbox update message'",
        "triggerBody()['text_3']": f"'{ME}'",
        "triggerBody()['text_4']": "'Sandbox student update'",
        "triggerBody()['text']": f"if(equals(triggerBody()?['Title'], 'badaddr'), 'not-an-email', '{ME}')",
    }
    for k, v in rep.items():
        t = t.replace(k, v)
    defn["actions"] = json.loads(t)
    pkg.definition = d
