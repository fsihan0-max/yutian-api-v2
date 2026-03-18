import uuid
from copy import deepcopy
from typing import Any, Dict, List

from ..utils.time_utils import utc_now_iso
from .json_repository import REVIEWS_FILE, read_json_list, write_json_list


def _normalize_review(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": item.get("id") or uuid.uuid4().hex[:10],
        "case_id": item.get("case_id") or item.get("caseId") or "",
        "reviewer": item.get("reviewer") or "系统用户",
        "corrected_label": item.get("corrected_label") or item.get("correctedLabel") or "",
        "corrected_area_mu": item.get("corrected_area_mu") if item.get("corrected_area_mu") is not None else item.get("correctedAreaMu", ""),
        "comment": item.get("comment") or "",
        "requires_resurvey": bool(item.get("requires_resurvey", item.get("requiresResurvey", False))),
        "created_at": item.get("created_at") or item.get("createdAt") or utc_now_iso(),
    }


def list_reviews() -> List[Dict[str, Any]]:
    items = read_json_list(REVIEWS_FILE)
    rows = [_normalize_review(item) for item in items if isinstance(item, dict)]
    return sorted(rows, key=lambda item: str(item.get("created_at", "")), reverse=True)


def create_review(payload: Dict[str, Any]) -> Dict[str, Any]:
    review = _normalize_review(
        {
            "id": uuid.uuid4().hex[:10],
            "case_id": payload.get("case_id", ""),
            "reviewer": payload.get("reviewer", "系统用户"),
            "corrected_label": payload.get("corrected_label", ""),
            "corrected_area_mu": payload.get("corrected_area_mu", ""),
            "comment": payload.get("comment", ""),
            "requires_resurvey": bool(payload.get("requires_resurvey", False)),
            "created_at": utc_now_iso(),
        }
    )

    items = list_reviews()
    items.append(review)
    write_json_list(REVIEWS_FILE, items)
    return deepcopy(review)


def count_reviews() -> int:
    return len(list_reviews())
