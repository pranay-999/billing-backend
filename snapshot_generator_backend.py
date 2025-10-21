#!/usr/bin/env python3
import os, re, json, hashlib
from datetime import datetime
from pathlib import Path

OUTPUT_JSON = "backend_snapshot.json"
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

def main():
    files = collect_files()
    snapshot = {
        "type": "backend",
        "generated_at": datetime.utcnow().isoformat()+"Z",
        "files": files,
        "routes": extract_flask_routes(files),
        "meta": {"total_files": len(files)}
    }
    Path(OUTPUT_JSON).write_text(json.dumps(snapshot, indent=2))
    print(f"✅ Backend snapshot created with {len(files)} files")

if __name__ == "__main__":
    main()
