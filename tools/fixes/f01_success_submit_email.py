"""Flow #1 — UTP/CSD/CDO Success Submit Email.

Findings: refdocs/issues/2026-09-30-flow-01-success-submit-email.md
- Outlook send failure (bad/blank address, connection expired) -> flow stops, nobody told.
- Existing backup path runs only on TimedOut, never on Failed, and uses the SharePoint
  SendEmail API that Microsoft retired on 2025-10-31 -> dead code.

Fix: Try/Catch. Send the email inside a Try scope; on Failed/TimedOut, look up the shared
Teams config item (same one every other flow uses) and alert staff with the student, the
address, the error and a run link; then Terminate as Failed so run history tells the truth.
"""

SOURCE_ZIP = "flows/UTPCSDCDO Success Submit Email.zip"
DISPLAY_NAME = "UTP/CSD/CDO Success Submit Email"
SITE = "https://utpmy.sharepoint.com/sites/CareerDevelopmentOfficeCDO"
CONFIG_LIST = "be7f2b53-cc4e-42b1-a043-a7d6a849ba42"

TRY = "Try_-_Send_confirmation_email"
# Two shapes seen in the sandbox: a malformed address sets result.error.message (T3); a blank one leaves
# error.message null and puts the connector error in outputs.body.error.message (T4). Raw JSON was the
# fallback and looked awful in Teams, so it now only appears if neither message exists.
ERROR_EXPR = (
    f"coalesce(first(result('{TRY}'))?['error']?['message'], "
    f"first(result('{TRY}'))?['outputs']?['body']?['error']?['message'], "
    f"string(first(result('{TRY}'))?['outputs']?['body']), 'not available')"
)
RUN_LINK = (
    "https://make.powerautomate.com/environments/@{workflow()?['tags']?['environmentName']}"
    "/flows/@{workflow()?['name']}/runs/@{workflow()?['run']?['name']}"
)
ALERT_HTML = (
    '<p><span style="color: rgb(0,0,0)">Flow Name: ' + DISPLAY_NAME + "<br>\n"
    "Date Time: @{convertTimeZone(utcNow(), 'UTC', 'Singapore Standard Time', 'dd/MM/yy hh:mm:ss tt')}<br>\n<br>\n"
    'The student confirmation email is </span><span style="color: rgb(184,49,47)">FAILED</span>'
    '<span style="color: rgb(0,0,0)">!<br>\n<br>\n'
    "Student: @{triggerOutputs()?['body/field_2']}<br>\n"
    "Email: @{triggerOutputs()?['body/field_5']}<br>\n"
    "List item ID: @{triggerOutputs()?['body/ID']}<br>\n"
    "Error: @{" + ERROR_EXPR + "}<br>\n"
    '<a href="' + RUN_LINK + '">Open this run</a></span></p>'
)


def apply(pkg):
    pkg.add_connector("shared_teams_1", "teams", "Microsoft Teams")
    d = pkg.definition
    acts = d["properties"]["definition"]["actions"]

    send = acts["Send_an_email_(V2)"]
    send["runAfter"] = {}

    new_actions = {
        TRY: {"type": "Scope", "runAfter": {}, "actions": {"Send_an_email_(V2)": send}},
        "Catch_-_Alert_CDO_staff": {
            "type": "Scope",
            "runAfter": {TRY: ["Failed", "TimedOut"]},
            "actions": {
                "Get_item": {
                    "type": "OpenApiConnection",
                    "runAfter": {},
                    "inputs": {
                        "host": {
                            "apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
                            "connectionName": "shared_sharepointonline",
                            "operationId": "GetItem",
                        },
                        "parameters": {"dataset": SITE, "table": CONFIG_LIST, "id": 1},
                        "authentication": "@parameters('$authentication')",
                    },
                },
                "Post_failure_alert_to_Teams": {
                    "type": "OpenApiConnection",
                    "runAfter": {"Get_item": ["Succeeded"]},
                    "inputs": {
                        "host": {
                            "apiId": "/providers/Microsoft.PowerApps/apis/shared_teams",
                            "connectionName": "shared_teams_1",
                            "operationId": "PostMessageToConversation",
                        },
                        "parameters": {
                            "poster": "Flow bot",
                            "location": "Chat with Flow bot",
                            "body/recipient": "@{outputs('Get_item')?['body/TeamsNotification1']};",
                            "body/messageBody": ALERT_HTML,
                            "body/isAlert": True,
                        },
                        "authentication": "@parameters('$authentication')",
                    },
                },
            },
        },
        "Terminate_-_Mark_run_as_failed": {
            "type": "Terminate",
            "runAfter": {"Catch_-_Alert_CDO_staff": ["Succeeded", "Failed", "TimedOut"]},
            "inputs": {
                "runStatus": "Failed",
                "runError": {
                    "code": "ConfirmationEmailFailed",
                    "message": "Confirmation email to @{triggerOutputs()?['body/field_5']} failed: @{" + ERROR_EXPR + "}",
                },
            },
        },
    }
    # The old TimedOut-only backup (Compose + SharePoint SendEmail API, retired 2025-10-31) is dropped.
    d["properties"]["definition"]["actions"] = new_actions
    pkg.definition = d
