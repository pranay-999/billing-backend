#!/usr/bin/env python3
"""
snapshot_generator_backend.py
--------------------------------
Generates backend snapshot with routes + dependencies.
"""
import os, re, json, hashlib, zipfile, subprocess
from datetime import datetime
from pathlib import Path

OUTPUT_JSON = "backend_snapshot.json"
OUTPUT_ZIP = "backend_snapshot.zip"
HISTORY_FILE = "snapshot_history.json"
HISTORY_LIMIT = 5
INCLUDE_EXTS = {".py", ".txt", ".sql", ".json", ".md"}
EXCLUDE_DIRS = {".git", ".venv", "__pycache__", "migrations"}

def sha256(d): return hashlib.sha256(d).hexdigest()
def is_excluded(p): return any(part in EXCLUDE_DIRS for part in p.parts)

def collect_files(base="."):
    base = Path(base)
    out = {}
    for path in base.rglob("*"):
        if path.is_file() and not is_excluded(path) and path.suffix in INCLUDE_EXTS:
            text = path.read_text(encoding="utf-8", errors="ignore")
            out[str(path.relative_to(base))] = {
                "content": text[:200000],
                "sha256": sha256(text.encode()),
                "size": len(text),
            }
    return out

def extract_flask_routes(files):
    routes = []
    pattern = re.compile(r"@(?:app|bp)\.route\(['\"](.*?)['\"]")
    for name, data in files.items():
        if name.endswith(".py"):
            for r in pattern.findall(data["content"]):
                routes.append({"file": name, "route": r})
    return routes

def get_git_commit():
    try: return subprocess.check_output(["git","rev-parse","HEAD"]).decode().strip()
    except: return "unknown"

def get_dependencies():
    req = Path("requirements.txt")
    if req.exists():
        return [l.strip() for l in req.read_text().splitlines() if l.strip() and not l.startswith("#")]
    return []

def make_zip(snapshot):
    with zipfile.ZipFile(OUTPUT_ZIP,"w",zipfile.ZIP_DEFLATED) as z:
        for path, data in snapshot["files"].items():
            z.writestr(path, data.get("content",""))
    print(f"🗜 Created {OUTPUT_ZIP}")

def update_history(meta):
    hist = []
    if Path(HISTORY_FILE).exists():
        try: hist = json.loads(Path(HISTORY_FILE).read_text())
        except: pass
    hist.insert(0, meta)
    hist = hist[:HISTORY_LIMIT]
    Path(HISTORY_FILE).write_text(json.dumps(hist, indent=2))

def main():
    files = collect_files()
    snapshot = {
        "type": "backend",
        "generated_at": datetime.utcnow().isoformat()+"Z",
        "git_commit": get_git_commit(),
        "dependencies": get_dependencies(),
        "routes": extract_flask_routes(files),
        "files": files,
        "meta": {"total_files": len(files)}
    }
    Path(OUTPUT_JSON).write_text(json.dumps(snapshot, indent=2))
    make_zip(snapshot)
    update_history({"timestamp": snapshot["generated_at"], "commit": snapshot["git_commit"], "total_files": len(files)})
    print(f"✅ Snapshot ready: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
