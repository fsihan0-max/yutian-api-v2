from typing import Any, Dict, List

from .json_repository import SAMPLES_FILE, read_json_list


def list_samples() -> List[Dict[str, Any]]:
    items = read_json_list(SAMPLES_FILE)
    return [item for item in items if isinstance(item, dict)]
