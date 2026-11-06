"""Shared paths and JSON helpers. Standard library only, so CI needs no installs."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
BUILD = DATA / "build"
FIXTURES = DATA / "fixtures"
CACHE = DATA / "cache"
ENRICH = DATA / "enrich"
REPORTS = DATA / "reports"
OUT = ROOT / "public" / "data"

AWARDS_FILE = RAW / "oscars.tsv"
NORMALIZED_FILE = BUILD / "normalized.json"
USER_AGENT = "every-envelope-pipeline/0.1"


def write_json(path, payload):
    """Write compact UTF-8 JSON, creating parent folders as needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"  wrote {path.relative_to(ROOT)} ({len(text) / 1024:.0f} KB)")
    return path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
