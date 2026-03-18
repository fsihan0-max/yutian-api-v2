import uuid
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..schemas.contracts import (
    CASE_STATUS_ANALYZING,
    CASE_STATUS_CLOSED,
    CASE_STATUS_PENDING_REVIEW,
    CASE_STATUS_PENDING_SURVEY,
)
from ..utils.time_utils import utc_now_iso
from .json_repository import CASES_FILE, read_json_list, write_json_list


DEFAULT_CASES: List[Dict[str, Any]] = [
    {
        "id": "YT-20260316-001",
        "town": "城关镇",
        "village": "东关村",
        "crop": "小麦",
        "status": CASE_STATUS_PENDING_REVIEW,
        "reporter": "王建国",
        "surveyor": "查勘员1",
        "imageSource": "无人机 GeoTIFF",
        "disasterType": "物理倒伏",
        "confidence": 0.84,
        "recognizedAreaMu": 18.6,
        "result": "识别面积 18.6 亩，待复核确认。",
        "createdAt": "2026-03-16T01:30:00Z",
        "updatedAt": "2026-03-16T06:40:00Z",
        "riskScore": 0.76,
        "reviewLabel": "",
        "correctedAreaMu": "",
        "reviewer": "",
        "disputeStatus": "处理中",
        "timeline": [
            {"action": "案件创建", "at": "2026-03-16T01:30:00Z", "detail": "农户发起报案。"},
            {"action": "分析完成", "at": "2026-03-16T06:40:00Z", "detail": "查勘分析已提交复核。"},
        ],
    },
    {
        "id": "YT-20260316-002",
        "town": "柳泉镇",
        "village": "北坡村",
        "crop": "玉米",
        "status": CASE_STATUS_ANALYZING,
        "reporter": "赵红梅",
        "surveyor": "查勘员1",
        "imageSource": "Sentinel-2",
        "disasterType": "待判定",
        "confidence": 0.56,
        "recognizedAreaMu": 0,
        "result": "正在执行耕地筛选与像元分类。",
        "createdAt": "2026-03-16T03:20:00Z",
        "updatedAt": "2026-03-16T03:30:00Z",
        "riskScore": 0.58,
        "reviewLabel": "",
        "correctedAreaMu": "",
        "reviewer": "",
        "disputeStatus": "无",
        "timeline": [
            {"action": "案件创建", "at": "2026-03-16T03:20:00Z", "detail": "农户发起报案。"},
            {"action": "开始分析", "at": "2026-03-16T03:30:00Z", "detail": "已上传 AOI 并开始分析。"},
        ],
    },
    {
        "id": "YT-20260316-003",
        "town": "河湾镇",
        "village": "西陈村",
        "crop": "小麦",
        "status": CASE_STATUS_PENDING_SURVEY,
        "reporter": "陈玉兰",
        "surveyor": "查勘员1",
        "imageSource": "待上传",
        "disasterType": "待判定",
        "confidence": 0.5,
        "recognizedAreaMu": 0,
        "result": "等待外业证据。",
        "createdAt": "2026-03-16T05:10:00Z",
        "updatedAt": "2026-03-16T05:10:00Z",
        "riskScore": 0.43,
        "reviewLabel": "",
        "correctedAreaMu": "",
        "reviewer": "",
        "disputeStatus": "无",
        "timeline": [
            {"action": "案件创建", "at": "2026-03-16T05:10:00Z", "detail": "农户发起报案。"},
        ],
    },
]


def _now_iso() -> str:
    return utc_now_iso()


def _gen_case_id() -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    return f"YT-{today}-{uuid.uuid4().hex[:4].upper()}"


def _crop_text_from_mode(crop_mode: str) -> str:
    mapping = {"wheat": "小麦", "corn": "玉米"}
    return mapping.get(crop_mode, crop_mode or "未知")


def _append_timeline(case_item: Dict[str, Any], action: str, detail: str) -> None:
    timeline = case_item.get("timeline") if isinstance(case_item.get("timeline"), list) else []
    timeline.append({"action": action, "detail": detail, "at": _now_iso()})
    case_item["timeline"] = timeline


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_case(item: Dict[str, Any]) -> Dict[str, Any]:
    now = _now_iso()
    crop_mode = str(item.get("cropMode") or item.get("crop_mode") or "wheat")
    model_mode = str(item.get("modelMode") or item.get("model_mode") or "rule")
    review_label = item.get("reviewLabel")
    if review_label is None:
        review_label = item.get("review_label")
    if review_label is None:
        review_label = item.get("corrected_label")

    corrected_area = item.get("correctedAreaMu")
    if corrected_area is None:
        corrected_area = item.get("corrected_area_mu")
    if corrected_area is None:
        corrected_area = ""

    normalized = {
        "id": str(item.get("id") or ""),
        "town": item.get("town") or "未知乡镇",
        "village": item.get("village") or "未知村",
        "crop": item.get("crop") or _crop_text_from_mode(crop_mode),
        "status": item.get("status") or CASE_STATUS_PENDING_SURVEY,
        "reporter": item.get("reporter") or "系统用户",
        "surveyor": item.get("surveyor") or "查勘员1",
        "imageSource": item.get("imageSource") or item.get("image_source") or "待上传",
        "disasterType": item.get("disasterType") or item.get("disaster_type") or "待判定",
        "confidence": _to_float(item.get("confidence"), 0.0),
        "recognizedAreaMu": _to_float(item.get("recognizedAreaMu", item.get("recognized_area_mu")), 0.0),
        "result": item.get("result") or "等待分析",
        "createdAt": item.get("createdAt") or item.get("created_at") or now,
        "updatedAt": item.get("updatedAt") or item.get("updated_at") or now,
        "riskScore": _to_float(item.get("riskScore", item.get("risk_score")), 0.3),
        "timeline": item.get("timeline") if isinstance(item.get("timeline"), list) else [],
        "reviewLabel": review_label or "",
        "correctedAreaMu": corrected_area,
        "reviewer": item.get("reviewer") or "",
        "disputeStatus": item.get("disputeStatus") or item.get("dispute_status") or "无",
        "lastReportAction": item.get("lastReportAction") or item.get("last_report_action") or None,
        "cropMode": crop_mode,
        "modelMode": model_mode,
        "totalAreaMu": _to_float(item.get("totalAreaMu", item.get("total_area_mu")), 0.0),
        "effectiveAreaMu": _to_float(item.get("effectiveAreaMu", item.get("effective_area_mu")), 0.0),
        "filteredNonAgriAreaMu": _to_float(
            item.get("filteredNonAgriAreaMu", item.get("filtered_non_agri_area_mu")),
            0.0,
        ),
        "lastAnalysis": item.get("lastAnalysis") or item.get("last_analysis") or None,
        "lastReview": item.get("lastReview") or item.get("last_review") or None,
    }
    if not normalized["id"]:
        normalized["id"] = _gen_case_id()
    return normalized


def _load_cases_raw() -> List[Dict[str, Any]]:
    items = read_json_list(CASES_FILE)
    cases = [_normalize_case(item) for item in items if isinstance(item, dict)]
    if not cases:
        cases = [_normalize_case(deepcopy(seed)) for seed in DEFAULT_CASES]
        write_json_list(CASES_FILE, cases)
    return cases


def _save_cases(cases: List[Dict[str, Any]]) -> None:
    write_json_list(CASES_FILE, cases)


def _calc_risk_score(damage_ratio: float, confidence: float) -> float:
    return min(0.99, max(0.1, (damage_ratio * 0.65) + ((1 - confidence) * 0.35)))


def list_cases() -> List[Dict[str, Any]]:
    cases = _load_cases_raw()
    return sorted(cases, key=lambda item: str(item.get("updatedAt", "")), reverse=True)


def get_case(case_id: str) -> Optional[Dict[str, Any]]:
    for case_item in list_cases():
        if case_item.get("id") == case_id:
            return case_item
    return None


def _get_or_create_case(cases: List[Dict[str, Any]], case_id: str) -> Dict[str, Any]:
    for item in cases:
        if item.get("id") == case_id:
            return item

    now = _now_iso()
    case_item = _normalize_case(
        {
            "id": case_id,
            "status": CASE_STATUS_PENDING_SURVEY,
            "createdAt": now,
            "updatedAt": now,
            "timeline": [],
        }
    )
    _append_timeline(case_item, "案件创建", "系统创建案件记录。")
    cases.append(case_item)
    return case_item


def begin_analysis(
    case_id: str,
    operator: str,
    crop_mode: str,
    model_mode: str,
    area_mu: float,
    image_source: str,
) -> Dict[str, Any]:
    resolved_case_id = case_id or _gen_case_id()
    cases = _load_cases_raw()
    case_item = _get_or_create_case(cases, resolved_case_id)

    case_item["status"] = CASE_STATUS_ANALYZING
    case_item["cropMode"] = crop_mode
    case_item["modelMode"] = model_mode
    case_item["crop"] = _crop_text_from_mode(crop_mode)
    case_item["imageSource"] = image_source
    case_item["totalAreaMu"] = round(_to_float(area_mu), 2)
    case_item["result"] = "分析任务已提交，正在执行。"
    case_item["updatedAt"] = _now_iso()
    _append_timeline(case_item, "开始分析", f"{operator} 发起分析任务。")

    _save_cases(cases)
    return deepcopy(case_item)


def complete_analysis(case_id: str, operator: str, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    cases = _load_cases_raw()
    case_item = _get_or_create_case(cases, case_id)

    final_result = analysis_result.get("final_result", {}) if isinstance(analysis_result, dict) else {}
    damage_ratio = _to_float((analysis_result.get("state_ratios") or {}).get("damage"), 0.0)
    confidence = _to_float(final_result.get("confidence"), 0.0)

    case_item["status"] = CASE_STATUS_PENDING_REVIEW
    case_item["recognizedAreaMu"] = round(_to_float(analysis_result.get("recognized_area_mu")), 2)
    case_item["effectiveAreaMu"] = round(_to_float(analysis_result.get("effective_area_mu")), 2)
    case_item["filteredNonAgriAreaMu"] = round(_to_float(analysis_result.get("filtered_non_agri_area_mu")), 2)
    case_item["disasterType"] = final_result.get("label") or "待判定"
    case_item["confidence"] = confidence
    case_item["riskScore"] = _calc_risk_score(damage_ratio, confidence)
    case_item["result"] = f"分析完成：{case_item['disasterType']}，识别面积 {case_item['recognizedAreaMu']} 亩，待复核。"
    case_item["lastAnalysis"] = analysis_result
    case_item["updatedAt"] = _now_iso()
    _append_timeline(case_item, "分析完成", f"{operator} 完成分析并提交复核。")

    _save_cases(cases)
    return deepcopy(case_item)


def fail_analysis(case_id: str, operator: str, reason: str) -> Dict[str, Any]:
    cases = _load_cases_raw()
    case_item = _get_or_create_case(cases, case_id)

    case_item["status"] = CASE_STATUS_PENDING_SURVEY
    case_item["result"] = f"分析失败：{reason}"
    case_item["updatedAt"] = _now_iso()
    _append_timeline(case_item, "分析失败", f"{operator} 分析失败：{reason}")

    _save_cases(cases)
    return deepcopy(case_item)


def apply_review(case_id: str, review_item: Dict[str, Any], dispute_status: str) -> Dict[str, Any]:
    cases = _load_cases_raw()
    case_item = _get_or_create_case(cases, case_id)

    corrected_label = str(review_item.get("corrected_label", "") or "").strip()
    corrected_area = review_item.get("corrected_area_mu")
    reviewer = str(review_item.get("reviewer", "系统用户") or "系统用户")
    requires_resurvey = bool(review_item.get("requires_resurvey", False))

    case_item["reviewLabel"] = corrected_label
    case_item["correctedAreaMu"] = corrected_area
    case_item["reviewer"] = reviewer
    case_item["lastReview"] = review_item
    case_item["disputeStatus"] = dispute_status

    if corrected_label:
        case_item["disasterType"] = corrected_label
    if corrected_area not in (None, ""):
        case_item["recognizedAreaMu"] = round(_to_float(corrected_area), 2)

    if requires_resurvey:
        case_item["status"] = CASE_STATUS_PENDING_SURVEY
        case_item["result"] = "复核要求补充查勘，案件已回退至待查勘。"
        case_item["riskScore"] = max(_to_float(case_item.get("riskScore"), 0.5), 0.6)
        _append_timeline(case_item, "复核退回", f"{reviewer} 提交复核，要求重新查勘。")
    else:
        case_item["status"] = CASE_STATUS_CLOSED
        case_item["result"] = "复核完成并结案。"
        case_item["riskScore"] = 0.2
        _append_timeline(case_item, "复核结案", f"{reviewer} 提交复核并结案。")

    case_item["updatedAt"] = _now_iso()
    _save_cases(cases)
    return deepcopy(case_item)


def attach_last_report_action(case_id: str, report_action: Dict[str, Any]) -> Dict[str, Any]:
    cases = _load_cases_raw()
    case_item = _get_or_create_case(cases, case_id)
    case_item["lastReportAction"] = report_action
    case_item["updatedAt"] = _now_iso()
    _save_cases(cases)
    return deepcopy(case_item)
