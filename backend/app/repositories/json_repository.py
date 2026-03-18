import json
from pathlib import Path
from typing import Any, List

from ..config.settings import DATA_FIXTURE_DIR


SAMPLES_FILE = DATA_FIXTURE_DIR / "sample_labels.json"
REVIEWS_FILE = DATA_FIXTURE_DIR / "review_records.json"
CASES_FILE = DATA_FIXTURE_DIR / "case_records.json"
DISPUTES_FILE = DATA_FIXTURE_DIR / "dispute_records.json"
REPORTS_FILE = DATA_FIXTURE_DIR / "report_records.json"


def ensure_data_files() -> None:
    DATA_FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    for path in (SAMPLES_FILE, REVIEWS_FILE, CASES_FILE, DISPUTES_FILE, REPORTS_FILE):
        if not path.exists():
            path.write_text("[]", encoding="utf-8")


def read_json_list(path: Path) -> List[Any]:
    ensure_data_files()
    try:
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            return []
        data = json.loads(content)
        if isinstance(data, list):
            return data
        return []
    except json.JSONDecodeError:
        return []


def write_json_list(path: Path, data: List[Any]) -> None:
    ensure_data_files()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
