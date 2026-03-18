import uuid
from copy import deepcopy
from typing import Any, Dict, List

from ..utils.time_utils import utc_now_iso
from .json_repository import REPORTS_FILE, read_json_list, write_json_list


def _normalize_report(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": item.get("id") or f"RPT-{uuid.uuid4().hex[:8]}",
        "caseId": item.get("caseId") or item.get("case_id") or "",
        "caseStatus": item.get("caseStatus") or item.get("case_status") or "",
        "title": item.get("title") or "业务动作",
        "detail": item.get("detail") or "",
        "operator": item.get("operator") or "系统",
        "type": item.get("type") or "operation",
        "createdAt": item.get("createdAt") or item.get("created_at") or utc_now_iso(),
    }


def list_report_actions(case_id: str = "") -> List[Dict[str, Any]]:
    items = read_json_list(REPORTS_FILE)
    rows = [_normalize_report(item) for item in items if isinstance(item, dict)]
    if case_id:
        rows = [item for item in rows if item.get("caseId") == case_id]
    return sorted(rows, key=lambda item: str(item.get("createdAt", "")), reverse=True)


def append_report_action(
    case_id: str,
    case_status: str,
    operator: str,
    title: str,
    detail: str,
    action_type: str,
) -> Dict[str, Any]:
    record = {
        "id": f"RPT-{uuid.uuid4().hex[:8]}",
        "caseId": case_id,
        "caseStatus": case_status,
        "title": title,
        "detail": detail,
        "operator": operator,
        "type": action_type,
        "createdAt": utc_now_iso(),
    }

    rows = list_report_actions()
    rows.append(record)
    write_json_list(REPORTS_FILE, rows)
    return deepcopy(record)
