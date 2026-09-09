"""Check seed structure, Unity metadata, and export provenance without Unity."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "game/Assets"
errors = []


def require(condition, message):
    if not condition:
        errors.append(message)


for path in sorted(ROOT.rglob("*")):
    if any(part in {".git", "Library", "Temp", "Logs", "UserSettings", "__pycache__"}
           for part in path.relative_to(ROOT).parts):
        continue
    if path.suffix in {".json", ".asmdef"}:
        try:
            json.loads(path.read_text())
        except (ValueError, OSError) as error:
            errors.append(f"{path.relative_to(ROOT)}: {error}")

guids = {}
for meta in ASSETS.rglob("*.meta"):
    target = meta.with_suffix("")
    require(target.exists(), f"Orphan metadata: {meta.relative_to(ROOT)}")
    matches = re.findall(r"^guid: ([0-9a-f]{32})$", meta.read_text(), re.MULTILINE)
    require(len(matches) == 1, f"Invalid GUID: {meta.relative_to(ROOT)}")
    if matches:
        guid = matches[0]
        require(guid not in guids, f"Duplicate GUID: {meta.relative_to(ROOT)}")
        guids[guid] = meta

for path in ASSETS.rglob("*"):
    if path.suffix in {".cs", ".asmdef"} or path.is_dir():
        require(Path(str(path) + ".meta").exists(), f"Missing seed metadata: {path.relative_to(ROOT)}")

runtime = ASSETS / "_DarioKart/Scripts/Runtime"
for script in runtime.rglob("*.cs"):
    require("using UnityEditor" not in script.read_text(), f"Editor dependency in {script.name}")
require(not list(ASSETS.rglob("*.blend")), "Editable Blender sources belong outside Unity Assets.")

for manifest_path in ASSETS.rglob("*.export.json"):
    try:
        manifest = json.loads(manifest_path.read_text())
        for field, hash_field in [("source", "sourceSha256"), ("output", "outputSha256")]:
            path = (ROOT / manifest[field]).resolve()
            path.relative_to(ROOT)
            require(path.is_file(), f"Missing export {field}: {path}")
            if path.is_file():
                require(hashlib.sha256(path.read_bytes()).hexdigest() == manifest[hash_field],
                        f"Stale export provenance: {manifest_path.name} ({field})")
    except (ValueError, KeyError, OSError) as error:
        errors.append(f"Invalid export manifest {manifest_path}: {error}")

require((ROOT / "game/ProjectSettings/ProjectVersion.txt").is_file(), "Missing editor pin")
require((ROOT / "game/Packages/manifest.json").is_file(), "Missing Unity package manifest")
require((ROOT / "art-source/blender/props/pipeline_ramp.blend").is_file(), "Missing Blender pipeline fixture")
require((ASSETS / "_DarioKart/Art/Models/Props/pipeline_ramp.fbx").is_file(), "Missing FBX pipeline fixture")
if errors:
    print("\n".join(f"ERROR: {message}" for message in errors))
    sys.exit(1)
print(f"Repository checks passed ({len(guids)} unique Unity GUIDs).")
print("This does not compile C#, resolve Unity packages, or validate gameplay/rendering.")
