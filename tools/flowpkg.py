"""Read, patch, retarget and re-zip Power Automate legacy flow packages (.zip).

Used by tools/build.py. See refdocs/guides/sandbox_runbook.md for why this exists (D-08).
"""
import json
import re
import uuid
import zipfile

# Production identifiers that must never survive into a sandbox package.
PROD_MARKERS = ["CareerDevelopmentOfficeCDO", "kamalazreel"]
# Parameters that point a connector action at a concrete data location.
LOCATION_PARAMS = ("dataset", "table", "source", "drive", "file", "folderId", "folderPath")


class Package:
    def __init__(self, path):
        self.files = {}
        self.bom = {}
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                data = z.read(name)
                self.bom[name] = data.startswith(b"\xef\xbb\xbf")
                self.files[name] = data.decode("utf-8-sig") if name.endswith(".json") else data
        self.flow_dir = next(n.rsplit("/", 1)[0] for n in self.files if n.endswith("/definition.json"))
        self.flow_key = self.flow_dir.rsplit("/", 1)[1]

    # --- json accessors -------------------------------------------------
    def _get(self, name):
        return json.loads(self.files[name])

    def _put(self, name, obj):
        self.files[name] = json.dumps(obj, ensure_ascii=False)

    @property
    def definition(self):
        return self._get(f"{self.flow_dir}/definition.json")

    @definition.setter
    def definition(self, obj):
        self._put(f"{self.flow_dir}/definition.json", obj)

    @property
    def manifest(self):
        return self._get("manifest.json")

    @manifest.setter
    def manifest(self, obj):
        self._put("manifest.json", obj)

    # --- edits ------------------------------------------------------------
    def set_display_name(self, name):
        d = self.definition
        d["properties"]["displayName"] = name
        self.definition = d
        m = self.manifest
        m["resources"][self.flow_key]["details"]["displayName"] = name
        self.manifest = m

    def force_create_as_new(self):
        """Stop the import screen from defaulting to 'Update' — a sandbox copy must never overwrite a real flow."""
        m = self.manifest
        res = m["resources"][self.flow_key]
        res["suggestedCreationType"] = "New"
        res["creationType"] = "New"
        for r in m["resources"].values():
            if r.get("type") == "Microsoft.PowerApps/apis/connections":
                r["details"]["displayName"] = "(select your own connection)"
        self.manifest = m

    def add_connector(self, ref_name, api_name, display_name):
        """Declare a connector the original flow didn't use (e.g. Teams), in all four places a package needs it."""
        d = self.definition
        refs = d["properties"]["connectionReferences"]
        if ref_name in refs:
            return
        refs[ref_name] = {
            "connectionName": f"shared-{api_name}-placeholder",
            "source": "Embedded",
            "id": f"/providers/Microsoft.PowerApps/apis/shared_{api_name}",
            "tier": "NotSpecified",
            "apiName": api_name,
            "isProcessSimpleApiReferenceConversionAlreadyDone": False,
        }
        self.definition = d
        api_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{self.flow_key}/api/{api_name}"))
        conn_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{self.flow_key}/conn/{api_name}"))
        m = self.manifest
        m["resources"][api_id] = {
            "id": f"/providers/Microsoft.PowerApps/apis/shared_{api_name}",
            "name": f"shared_{api_name}",
            "type": "Microsoft.PowerApps/apis",
            "suggestedCreationType": "Existing",
            "details": {"displayName": display_name},
            "configurableBy": "System",
            "hierarchy": "Child",
            "dependsOn": [],
        }
        m["resources"][conn_id] = {
            "type": "Microsoft.PowerApps/apis/connections",
            "suggestedCreationType": "Existing",
            "creationType": "Existing",
            "details": {"displayName": "(select your own connection)"},
            "configurableBy": "User",
            "hierarchy": "Child",
            "dependsOn": [api_id],
        }
        m["resources"][self.flow_key]["dependsOn"] += [api_id, conn_id]
        self.manifest = m
        for fname, val in (("apisMap.json", api_id), ("connectionsMap.json", conn_id)):
            p = f"{self.flow_dir}/{fname}"
            mp = self._get(p)
            mp[ref_name] = val
            self._put(p, mp)

    def remove_connector(self, ref_name):
        """Drop a connector the harness doesn't use, from all four places a package declares it."""
        d = self.definition
        d["properties"]["connectionReferences"].pop(ref_name, None)
        self.definition = d
        ids = set()
        for fname in ("apisMap.json", "connectionsMap.json"):
            p = f"{self.flow_dir}/{fname}"
            mp = self._get(p)
            if ref_name in mp:
                ids.add(mp.pop(ref_name))
            self._put(p, mp)
        m = self.manifest
        for rid in ids:
            m["resources"].pop(rid, None)
        m["resources"][self.flow_key]["dependsOn"] = [
            x for x in m["resources"][self.flow_key]["dependsOn"] if x not in ids
        ]
        # a connection resource depends on its api resource; remove those orphans too
        for k, r in list(m["resources"].items()):
            if r.get("type") == "Microsoft.PowerApps/apis/connections" and any(x in ids for x in r.get("dependsOn", [])):
                m["resources"].pop(k)
                m["resources"][self.flow_key]["dependsOn"] = [x for x in m["resources"][self.flow_key]["dependsOn"] if x != k]
                for fname in ("connectionsMap.json",):
                    pass
        self.manifest = m

    def retarget(self, replace):
        """Swap production site/list/file identifiers for sandbox ones, then refuse to continue if any survive."""
        text = self.files[f"{self.flow_dir}/definition.json"]
        for prod, sandbox in replace.items():
            if sandbox.startswith("<"):
                if prod in text:
                    raise SystemExit(f"sandbox.json: '{prod}' is still a placeholder ({sandbox}) — fill it in first")
                continue
            text = text.replace(prod, sandbox)
        self.files[f"{self.flow_dir}/definition.json"] = text
        allowed = set(v for v in replace.values() if not v.startswith("<"))
        leftovers = [m for m in PROD_MARKERS if m in text]
        for key, val in _location_values(self.definition["properties"]["definition"]):
            if isinstance(val, str) and not val.startswith("@") and val not in allowed and not _is_path_under(val, allowed):
                leftovers.append(f"{key}={val}")
        if leftovers:
            raise SystemExit("Refusing to build sandbox package — production identifiers remain:\n  " + "\n  ".join(leftovers)
                             + "\nAdd a mapping for each to tools/sandbox.json.")

    def save(self, path):
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in self.files.items():
                if isinstance(data, str):
                    data = (b"\xef\xbb\xbf" if self.bom.get(name) else b"") + data.encode("utf-8")
                z.writestr(name, data)


def _location_values(node, key=""):
    if isinstance(node, dict):
        for k, v in node.items():
            if k in LOCATION_PARAMS:
                yield k, v
            yield from _location_values(v, k)
    elif isinstance(node, list):
        for v in node:
            yield from _location_values(v, key)


def _is_path_under(val, allowed):
    # Folder paths (e.g. /Shared Documents/...) are fine once the site itself is a sandbox site.
    return bool(re.match(r"^[/%]", val))


def walk_actions(actions):
    """Yield (name, action) for every action, including those nested in scopes/conditions/loops."""
    for name, act in actions.items():
        yield name, act
        yield from walk_actions(act.get("actions", {}))
        yield from walk_actions(act.get("else", {}).get("actions", {}))
        for case in act.get("cases", {}).values():
            yield from walk_actions(case.get("actions", {}))
        yield from walk_actions(act.get("default", {}).get("actions", {}))
