from typing import Any, Dict

from ..schemas.contracts import CASE_STATUS_CLOSED, CASE_STATUS_PENDING_SURVEY


def build_review_outcome(review_item: Dict[str, Any]) -> Dict[str, Any]:
    requires_resurvey = bool(review_item.get("requires_resurvey", False))
    corrected_label = str(review_item.get("corrected_label", "") or "").strip()

    if requires_resurvey:
        return {
            "next_status": CASE_STATUS_PENDING_SURVEY,
            "decision": "退回重查",
            "summary": "复核意见要求补充查勘，案件已回退。",
            "final_label": corrected_label or "待重查",
        }

    return {
        "next_status": CASE_STATUS_CLOSED,
        "decision": "复核结案",
        "summary": "复核意见确认后结案。",
        "final_label": corrected_label or "人工复核",
    }
