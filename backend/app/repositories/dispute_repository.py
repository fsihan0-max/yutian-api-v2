from copy import deepcopy
from typing import Any, Dict, List

from ..utils.time_utils import utc_now_iso
from .json_repository import DISPUTES_FILE, read_json_list, write_json_list


DEFAULT_DISPUTES = [
    {
        "id": "DSP-20260311-003",
        "caseId": "YT-20260316-001",
        "title": "YT-20260316-001",
        "detail": "农户对面积结果有异议，申请二次复核。",
        "status": "处理中",
        "createdAt": "2026-03-16T07:20:00Z",
    }
]


def _normalize_dispute(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": item.get("id") or f"DSP-{utc_now_iso().replace('-', '').replace(':', '').replace('T', '-').replace('Z', '')}",
        "caseId": item.get("caseId") or item.get("case_id") or "",
        "title": item.get("title") or item.get("caseId") or item.get("case_id") or "未绑定案件",
        "detail": item.get("detail") or "",
        "status": item.get("status") or "处理中",
        "createdAt": item.get("createdAt") or item.get("created_at") or utc_now_iso(),
        "updatedAt": item.get("updatedAt") or item.get("updated_at") or item.get("createdAt") or utc_now_iso(),
    }


def _load_disputes_raw() -> List[Dict[str, Any]]:
    items = read_json_list(DISPUTES_FILE)
    disputes = [_normalize_dispute(item) for item in items if isinstance(item, dict)]
    if not disputes:
        disputes = [_normalize_dispute(item) for item in DEFAULT_DISPUTES]
        write_json_list(DISPUTES_FILE, disputes)
    return disputes


def _save_disputes(disputes: List[Dict[str, Any]]) -> None:
    write_json_list(DISPUTES_FILE, disputes)


def list_disputes() -> List[Dict[str, Any]]:
    disputes = _load_disputes_raw()
    return sorted(disputes, key=lambda item: str(item.get("updatedAt", "")), reverse=True)


def update_dispute_from_review(case_id: str, reviewer: str, requires_resurvey: bool, comment: str = "") -> Dict[str, Any]:
    disputes = _load_disputes_raw()
    now = utc_now_iso()
    target = None
    for item in disputes:
        if item.get("caseId") == case_id:
            target = item
            break

    if target is None:
        target = _normalize_dispute({
            "id": f"DSP-{case_id}",
            "caseId": case_id,
            "title": case_id,
            "detail": "",
            "status": "处理中",
            "createdAt": now,
        })
        disputes.append(target)

    if requires_resurvey:
        target["status"] = "处理中"
        target["detail"] = comment or f"{reviewer} 要求补充查勘。"
    else:
        target["status"] = "已解决"
        base = comment or "复核确认后结案。"
        target["detail"] = f"{base}（{reviewer} 已处理）"

    target["updatedAt"] = now
    _save_disputes(disputes)
    return deepcopy(target)


def get_dispute_status(case_id: str) -> str:
    for item in list_disputes():
        if item.get("caseId") == case_id:
            return str(item.get("status") or "无")
    return "无"
