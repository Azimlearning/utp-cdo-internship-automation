"""PreToolUse guard for the Playwright browser tools (D-08: the personal account never touches production).

Blocks (exit 2, message back to Claude):
  * navigating to, or scripting against, the production CDO SharePoint site
  * any browser step that names a [LIVE-CDO] flow
  * uploading a flow package that isn't a sandbox build (build/baseline|fixed|fixedprobe|harness) - e.g. flows/*.zip,
    build/prod or build/probe (the probe/prod packages are for the office laptop only)
Scripts run from a file (browser_run_code_unsafe filename=...) are read and checked too.
Test it: python .claude/hooks/sandbox_guard.py --selftest
"""
import json
import pathlib
import re
import sys

PROD = [r"utpmy\.sharepoint\.com/sites/", r"CareerDevelopmentOfficeCDO", r"\[LIVE-CDO\]"]
PKG_OK = re.compile(r"[\\/]build[\\/](baseline|fixed|fixedprobe|baselinex|fixedx|harness)[\\/][^\\/]+\.zip$", re.I)


def problems(tool, inp):
    text = json.dumps(inp, ensure_ascii=False)
    if tool.endswith("browser_run_code_unsafe") and inp.get("filename"):
        try:
            text += pathlib.Path(inp["filename"]).read_text(encoding="utf-8")
        except OSError:
            pass
    out = [f"mentions production ({p.replace(chr(92), '')})" for p in PROD if re.search(p, text, re.I)]
    paths = list(inp.get("paths") or [])
    paths += re.findall(r"setInputFiles\(\s*['\"]([^'\"]+)['\"]", text)
    paths += re.findall(r'"zip":\s*"([^"]+)"', text)
    for p in paths:
        p = p.replace("\\\\", "\\")
        if p.lower().endswith(".zip") and not PKG_OK.search(p):
            out.append(f"uploads a package that is not a sandbox build: {p}")
    return out


def main():
    if sys.argv[1:] == ["--selftest"]:
        bad = [("mcp__playwright__browser_navigate", {"url": "https://utpmy.sharepoint.com/sites/CareerDevelopmentOfficeCDO/Lists"}),
               ("mcp__playwright__browser_click", {"element": "[LIVE-CDO] Combine raw data"}),
               ("mcp__playwright__browser_file_upload", {"paths": [r"c:\x\flows\[LIVE-CDO] UTPCSDCDO Combine raw data.zip"]}),
               ("mcp__playwright__browser_file_upload", {"paths": [r"c:\x\build\prod\flow07-prod.zip"]}),
               ("mcp__playwright__browser_file_upload", {"paths": [r"c:\x\build\probe\flow07-probe.zip"]})]
        good = [("mcp__playwright__browser_file_upload", {"paths": [r"c:\x\build\fixed\flow07-fixed.zip"]}),
                ("mcp__playwright__browser_file_upload", {"paths": [r"c:\x\build\fixedprobe\flow09-fixedprobe.zip"]}),
                ("mcp__playwright__browser_navigate", {"url": "https://utpmy-my.sharepoint.com/personal/me"})]
        ok = all(problems(t, i) for t, i in bad) and not any(problems(t, i) for t, i in good)
        print("selftest", "passed" if ok else "FAILED")
        sys.exit(0 if ok else 1)
    try:
        ev = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)
    found = problems(ev.get("tool_name", ""), ev.get("tool_input") or {})
    if found:
        print("Blocked by sandbox_guard (D-08: production is only touched at the office laptop): " + "; ".join(found),
              file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
