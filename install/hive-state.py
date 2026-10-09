"""Private ownership journal for the portable installer, never shell-sourced."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


def fingerprint(path):
    if path.is_symlink():
        return "link:" + os.readlink(path)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


directory = Path(sys.argv[1])
action = sys.argv[2]
manifest = directory / "state.json"
state = json.loads(manifest.read_text()) if manifest.exists() else {}

if action == "init":
    options = json.loads(sys.argv[3])
    if state and state["options"] != options:
        sys.exit("hive-install: installation options changed; uninstall with the original options first")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    directory.chmod(0o700)
    state.setdefault("options", options)
    state.setdefault("files", {})
elif action == "get":
    print(json.dumps(state.get(sys.argv[3], False)))
    sys.exit(0)
elif action == "set":
    state[sys.argv[3]] = json.loads(sys.argv[4])
elif action == "remember":
    path = Path(sys.argv[3])
    if str(path) not in state["files"]:
        backup = hashlib.sha256(str(path).encode()).hexdigest()
        existed = path.exists() or path.is_symlink()
        if existed:
            if not path.is_file() and not path.is_symlink():
                sys.exit(f"hive-install: refusing to replace non-file {path}")
            shutil.copy2(path, directory / backup, follow_symlinks=False)
        state["files"][str(path)] = {"existed": existed, "backup": backup}
elif action == "record":
    path = Path(sys.argv[3])
    state["files"][str(path)]["installed"] = fingerprint(path)
elif action == "restore":
    for name, info in reversed(list(state.get("files", {}).items())):
        path = Path(name)
        if "installed" not in info:
            print(f"kept file not successfully installed {path}")
            continue
        if fingerprint(path) != info.get("installed"):
            managed = state.get("managed_hooks", {})
            if name == managed.get("path") and path.exists():
                # Preserve later policy changes, removing only our hook entries.
                sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "share"))
                from hive_config import update
                update(path, managed["desired"], remove=True)
                print(f"removed Hive hooks from modified settings {path}")
                continue
            print(f"kept modified file {path}")
            continue
        if info["existed"]:
            path.unlink(missing_ok=True)
            shutil.copy2(directory / info["backup"], path, follow_symlinks=False)
            print(f"restored {path}")
        else:
            path.unlink(missing_ok=True)
            print(f"removed {path}")
    sys.exit(0)
else:
    sys.exit(f"unknown state action: {action}")

fd, temporary = tempfile.mkstemp(prefix="state.", dir=directory)
with os.fdopen(fd, "w") as stream:
    json.dump(state, stream, indent=2)
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
os.replace(temporary, manifest)
