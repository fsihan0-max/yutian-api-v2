import json
from dataclasses import dataclass
from typing import Any, Dict, Optional


CASE_STATUS_PENDING_SURVEY = "待查勘"
CASE_STATUS_ANALYZING = "分析中"
CASE_STATUS_PENDING_REVIEW = "待复核"
CASE_STATUS_CLOSED = "已结案"


def _parse_geometry(geometry_raw: Any) -> Optional[Dict[str, Any]]:
    if geometry_raw in (None, "", {}):
        return None

    geometry = geometry_raw
    if isinstance(geometry_raw, str):
        geometry = json.loads(geometry_raw)

    if not isinstance(geometry, dict):
        raise ValueError("空间坐标格式错误")

    if geometry.get("type") == "Polygon" and isinstance(geometry.get("coordinates"), list):
        return {"type": "Polygon", "coordinates": geometry["coordinates"]}

    rings = geometry.get("rings")
    if isinstance(rings, list) and rings:
        return {"type": "Polygon", "coordinates": rings}

    raise ValueError("未接收到空间坐标")


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _parse_optional_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    return float(value)


@dataclass
class AnalyzeRequest:
    geometry: Dict[str, Any]
    area_mu: float
    crop_mode: str
    model_mode: str
    case_id: str
    operator: str
    file_bytes: Optional[bytes] = None
    file_name: str = ""

    @classmethod
    def from_raw(cls, raw: Dict[str, Any]) -> "AnalyzeRequest":
        content_type = str(raw.get("content_type") or "")
        is_multipart = "multipart/form-data" in content_type
        payload = raw.get("form") if is_multipart else raw.get("json")
        payload = payload or {}
        if not isinstance(payload, dict):
            raise ValueError("请求体格式错误")

        geometry = _parse_geometry(payload.get("geometry"))
        if geometry is None:
            raise ValueError("未接收到空间坐标")

        area_mu = float(payload.get("area_mu", 0) or 0)
        crop_mode = str(payload.get("crop_mode", "wheat") or "wheat")
        model_mode = str(payload.get("model_mode", "rule") or "rule")
        case_id = str(payload.get("case_id", "") or "").strip()
        operator = str(payload.get("operator", "系统用户") or "系统用户").strip() or "系统用户"
        file_bytes = raw.get("file_bytes")
        file_name = str(raw.get("file_name", "") or "")

        return cls(
            geometry=geometry,
            area_mu=area_mu,
            crop_mode=crop_mode,
            model_mode=model_mode,
            case_id=case_id,
            operator=operator,
            file_bytes=file_bytes,
            file_name=file_name,
        )


@dataclass
class ReviewSubmitRequest:
    case_id: str
    reviewer: str
    corrected_label: str
    corrected_area_mu: Optional[float]
    comment: str
    requires_resurvey: bool

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "ReviewSubmitRequest":
        payload = payload or {}
        if not isinstance(payload, dict):
            raise ValueError("请求体格式错误")

        case_id = str(payload.get("case_id", "") or "").strip()
        if not case_id:
            raise ValueError("缺少案件编号 case_id")

        reviewer = str(payload.get("reviewer", "系统用户") or "系统用户").strip() or "系统用户"
        corrected_label = str(payload.get("corrected_label", "") or "").strip()
        corrected_area_mu = _parse_optional_float(payload.get("corrected_area_mu"))
        comment = str(payload.get("comment", "") or "").strip()
        requires_resurvey = _parse_bool(payload.get("requires_resurvey", False))

        return cls(
            case_id=case_id,
            reviewer=reviewer,
            corrected_label=corrected_label,
            corrected_area_mu=corrected_area_mu,
            comment=comment,
            requires_resurvey=requires_resurvey,
        )


def build_success_response(data: Dict[str, Any], snapshot: Dict[str, Any], message: str = "") -> Dict[str, Any]:
    return {
        "status": "success",
        "message": message,
        "data": data,
        "snapshot": snapshot,
    }


def build_error_response(message: str, snapshot: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "status": "error",
        "message": message,
        "data": data or {},
        "snapshot": snapshot or {},
        "error": message,
    }
