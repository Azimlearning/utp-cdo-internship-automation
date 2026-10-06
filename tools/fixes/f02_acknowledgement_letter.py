"""Flow #2 — Acknowledgement Letter Email Process (UI: "Issuance Letter Drop File").

Findings: refdocs/issues/2026-09-30-flow-02-acknowledgement-letter.md

Fix in this module: replace the deprecated trigger "When a file is created in a folder (deprecated)"
(OnNewFile) with "When a file is created (properties only)" (GetOnNewFileItems) + a Get file content action.

The old trigger handed the flow three things; the new one hands over none of them in the same shape:
  content  triggerOutputs()['body']                         -> body('Get_file_content_-_Dropped_file')
  name     triggerOutputs()['headers/x-ms-file-name-encoded'] -> triggerOutputs()['body/{FilenameWithExtension}']
  path     triggerOutputs()['headers/x-ms-file-path-encoded'] -> {FullPath} for path actions, {Identifier} for MoveFile

The trigger is proven on a harness first (tools build.py 2 harness) because flow 2's Excel scripts, Word template
and approvals can't run in a sandbox. Nothing else in the flow is changed here.
"""
import json

SOURCE_ZIP = "flows/[LIVE-CDO] UTPCSDCDO Acknowledgement Letter Email Process.zip"
DISPLAY_NAME = "UTP/CSD/CDO Acknowledgement Letter Email Process"
HARNESS_SKELETON_ZIP = "flows/UTPCSDCDO Success Submit Email.zip"  # SharePoint-trigger skeleton to build the harness from

SITE = "https://utpmy.sharepoint.com/sites/CareerDevelopmentOfficeCDO"
DOCS_LIBRARY = "3db2d009-d5dd-4ef0-bb47-ee85e8072a7d"  # the CDO 'Documents' library GUID, seen in flow 2's own actions
# Folder format for the new trigger is confirmed by the harness run (see the issue doc), then set here.
DROP_FOLDER = "/Shared Documents/Power Automate Documents/[UTP_CSD_CDO_AppointmentLetter]/Drop File"

GET_CONTENT = "Get_file_content_-_Dropped_file"
OLD_TRIGGER = "When_a_file_is_created_in_a_folder_(deprecated)"
NEW_TRIGGER = "When_a_file_is_created_(properties_only)"

SP_HOST = {
    "apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
    "connectionName": "shared_sharepointonline",
}


def new_trigger(site, library, folder, leaf="Drop File"):
    """`leaf` = the watched folder's own name, used by the 'direct child only' guard (shared with flow 14)."""
    return {
        NEW_TRIGGER: {
            "recurrence": {"frequency": "Minute", "interval": 1},
            "splitOn": "@triggerOutputs()?['body/value']",
            "conditions": [
                {"expression": "@equals(triggerBody()?['{IsFolder}'], false)"},
                # Parity with the old trigger, which ignored files in subfolders. {Path} looked like
                # 'Documents/CDO-Sandbox/Drop File/' (harness run 2026-09-30); nothing after 'Drop File/' = direct child.
                # Works whatever the library is called. UNTESTED as a trigger condition — re-run harness T-H4b.
                {"expression": "@equals(last(split(triggerBody()?['{Path}'], '" + leaf + "/')), '')"},
            ],
            "type": "OpenApiConnection",
            "inputs": {
                "host": {**SP_HOST, "operationId": "GetOnNewFileItems"},
                "parameters": {"dataset": site, "table": library, "folderPath": folder},
                "authentication": "@parameters('$authentication')",
            },
        }
    }


def get_content_action(run_after=None):
    return {
        "type": "OpenApiConnection",
        "runAfter": run_after or {},
        "inputs": {
            "host": {**SP_HOST, "operationId": "GetFileContent"},
            "parameters": {
                "dataset": SITE,
                "id": "@triggerOutputs()?['body/{Identifier}']",
                "inferContentType": True,
            },
            "authentication": "@parameters('$authentication')",
        },
    }


def apply(pkg):
    d = pkg.definition
    defn = d["properties"]["definition"]
    assert OLD_TRIGGER in defn["triggers"], "flow 2 no longer has the deprecated trigger — already fixed?"
    defn["triggers"] = new_trigger(SITE, DOCS_LIBRARY, DROP_FOLDER)

    # Dropped file content is fetched first; the main chain waits for it via the Scope.
    defn["actions"][GET_CONTENT] = get_content_action()
    scope = defn["actions"]["Scope_-_Create_new_folder_and_files"]
    scope["runAfter"][GET_CONTENT] = ["Succeeded"]

    from flowpkg import walk_actions

    for name, act in walk_actions(defn["actions"]):
        p = act.get("inputs", {}).get("parameters", {}) if isinstance(act.get("inputs"), dict) else {}
        for key, val in list(p.items()):
            if val == "@triggerOutputs()?['body']":
                p[key] = f"@body('{GET_CONTENT}')"
            elif val == "@triggerOutputs()?['headers/x-ms-file-path-encoded']":
                p[key] = (
                    "@triggerOutputs()?['body/{Identifier}']"
                    if name.startswith("Move_file")
                    else "@triggerOutputs()?['body/{FullPath}']"
                )
            elif isinstance(val, str) and "@{triggerOutputs()?['headers/x-ms-file-name-encoded']}" in val:
                p[key] = val.replace(
                    "@{triggerOutputs()?['headers/x-ms-file-name-encoded']}",
                    "@{triggerOutputs()?['body/{FilenameWithExtension}']}",
                )
    pkg.definition = d

    leftovers = [w for w in ("headers/x-ms-file", "triggerOutputs()?['body']") if w in json.dumps(pkg.definition)]
    if leftovers:
        raise SystemExit(f"flow 2 fix left old trigger references behind: {leftovers}")


# tools/sandbox/pw.py filetest 02 guard   (T-H4b: the subfolder guard as a live trigger condition)
FILETESTS = {
    "guard": {"watched": "/Documents/CDO-Sandbox/Drop File", "archive": "/Documents/CDO-Sandbox/Archive",
              "copiesIn": "/Documents/CDO-Sandbox", "copyPrefix": "[CLEANED]_", "expectRuns": 1, "settle": 150,
              "files": [{"folder": "/Documents/CDO-Sandbox/Drop File", "name": "G1 direct file.xlsx", "expectProcessed": True},
                        {"folder": "/Documents/CDO-Sandbox/Drop File/Sub", "name": "G2 in subfolder.xlsx", "expectProcessed": False}]},
}


def harness(pkg, cfg):
    """A minimal flow that exercises exactly the trigger-dependent parts of flow 2 against the sandbox library."""
    h = cfg["harness"]
    site, lib, root = cfg["replace"][SITE], h["library"], h["root"]
    d = pkg.definition
    defn = d["properties"]["definition"]
    defn["triggers"] = new_trigger(site, lib, f"{root}/Drop File")
    a = {}
    a[GET_CONTENT] = get_content_action()
    a[GET_CONTENT]["inputs"]["parameters"]["dataset"] = site
    a["Get_file_metadata_using_path"] = {
        "type": "OpenApiConnection",
        "runAfter": {GET_CONTENT: ["Succeeded"]},
        "inputs": {
            "host": {**SP_HOST, "operationId": "GetFileMetadataByPath"},
            "parameters": {"dataset": site, "path": "@triggerOutputs()?['body/{FullPath}']"},
            "authentication": "@parameters('$authentication')",
        },
    }
    a["Create_file_-_DuplicateDatabaseFile"] = {
        "type": "OpenApiConnection",
        "runAfter": {"Get_file_metadata_using_path": ["Succeeded"]},
        "inputs": {
            "host": {**SP_HOST, "operationId": "CreateFile"},
            "parameters": {
                "dataset": site,
                "folderPath": root,
                "name": "[CLEANED]_@{triggerOutputs()?['body/{FilenameWithExtension}']}",
                "body": f"@body('{GET_CONTENT}')",
            },
            "authentication": "@parameters('$authentication')",
        },
    }
    a["Compose_-_What_the_trigger_gave_us"] = {
        "type": "Compose",
        "runAfter": {"Create_file_-_DuplicateDatabaseFile": ["Succeeded"]},
        "inputs": {
            "FilenameWithExtension": "@triggerOutputs()?['body/{FilenameWithExtension}']",
            "FullPath": "@triggerOutputs()?['body/{FullPath}']",
            "Path": "@triggerOutputs()?['body/{Path}']",
            "Identifier": "@triggerOutputs()?['body/{Identifier}']",
            "IsFolder": "@triggerOutputs()?['body/{IsFolder}']",
            "OriginalSize": "@outputs('Get_file_metadata_using_path')?['body/Size']",
            "CopySize": "@outputs('Create_file_-_DuplicateDatabaseFile')?['body/Size']",
            "SameSize": "@equals(outputs('Get_file_metadata_using_path')?['body/Size'], outputs('Create_file_-_DuplicateDatabaseFile')?['body/Size'])",
        },
    }
    a["Move_file_-_Excel_File"] = {
        "type": "OpenApiConnection",
        "runAfter": {"Compose_-_What_the_trigger_gave_us": ["Succeeded"]},
        "inputs": {
            "host": {**SP_HOST, "operationId": "MoveFileAsync"},
            "parameters": {
                "dataset": site,
                "parameters/sourceFileId": "@triggerOutputs()?['body/{Identifier}']",
                "parameters/destinationDataset": site,
                "parameters/destinationFolderPath": f"{root}/Archive",
                "parameters/nameConflictBehavior": 1,
            },
            "authentication": "@parameters('$authentication')",
        },
    }
    defn["actions"] = a
    pkg.definition = d
    pkg.remove_connector("shared_office365")
