from typing import Any, Dict, Tuple

from ..algorithms.damage_analysis import run_damage_analysis
from ..repositories.case_repository import (
    attach_last_report_action,
    begin_analysis,
    complete_analysis,
    fail_analysis,
)
from ..repositories.report_repository import append_report_action
from ..schemas.contracts import AnalyzeRequest, build_error_response, build_success_response
from .domain_snapshot_service import build_domain_snapshot


def _build_analysis_data(
    analysis_result: Dict[str, Any],
    case_snapshot: Dict[str, Any],
    report_action: Dict[str, Any],
    snapshot: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "analysis": analysis_result,
        "case": case_snapshot,
        "latest_case": case_snapshot,
        "report_action": report_action,
        "workbench_refresh": snapshot.get("workbench_refresh", {}),
    }


def handle_analyze(raw_request: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    try:
        analyze_request = AnalyzeRequest.from_raw(raw_request)
    except ValueError as exc:
        body = build_error_response(str(exc), data={"case": {}})
        return body, 400

    image_source = "无人机高分影像" if analyze_request.file_bytes else "Sentinel-2"
    case_snapshot = begin_analysis(
        case_id=analyze_request.case_id,
        operator=analyze_request.operator,
        crop_mode=analyze_request.crop_mode,
        model_mode=analyze_request.model_mode,
        area_mu=analyze_request.area_mu,
        image_source=image_source,
    )
    case_id = str(case_snapshot.get("id", "") or "")

    start_action = append_report_action(
        case_id=case_id,
        case_status=case_snapshot.get("status", ""),
        operator=analyze_request.operator,
        title="分析开始",
        detail=f"{analyze_request.operator} 已发起分析任务。",
        action_type="analysis_start",
    )
    case_snapshot = attach_last_report_action(case_id, start_action)

    try:
        analysis_result = run_damage_analysis(
            {
                "geometry": analyze_request.geometry,
                "area_mu": analyze_request.area_mu,
                "crop_mode": analyze_request.crop_mode,
                "model_mode": analyze_request.model_mode,
                "file_bytes": analyze_request.file_bytes,
                "file_name": analyze_request.file_name,
            }
        )
        case_snapshot = complete_analysis(
            case_id=case_id,
            operator=analyze_request.operator,
            analysis_result=analysis_result,
        )
        done_action = append_report_action(
            case_id=case_id,
            case_status=case_snapshot.get("status", ""),
            operator=analyze_request.operator,
            title="分析完成",
            detail=f"{analyze_request.operator} 完成分析并提交复核。",
            action_type="analysis_done",
        )
        case_snapshot = attach_last_report_action(case_id, done_action)
        snapshot = build_domain_snapshot(case_id)
        body = build_success_response(
            data=_build_analysis_data(analysis_result, case_snapshot, done_action, snapshot),
            snapshot=snapshot,
            message="分析完成",
        )
        return body, 200
    except ValueError as exc:
        case_snapshot = fail_analysis(case_id=case_id, operator=analyze_request.operator, reason=str(exc))
        fail_action = append_report_action(
            case_id=case_id,
            case_status=case_snapshot.get("status", ""),
            operator=analyze_request.operator,
            title="分析失败",
            detail=str(exc),
            action_type="analysis_failed",
        )
        case_snapshot = attach_last_report_action(case_id, fail_action)
        snapshot = build_domain_snapshot(case_id)
        body = build_error_response(
            str(exc),
            snapshot=snapshot,
            data={
                "case": case_snapshot,
                "latest_case": case_snapshot,
                "report_action": fail_action,
                "workbench_refresh": snapshot.get("workbench_refresh", {}),
            },
        )
        return body, 400
    except Exception as exc:
        reason = f"分析失败: {str(exc)}"
        case_snapshot = fail_analysis(case_id=case_id, operator=analyze_request.operator, reason=reason)
        fail_action = append_report_action(
            case_id=case_id,
            case_status=case_snapshot.get("status", ""),
            operator=analyze_request.operator,
            title="分析失败",
            detail=reason,
            action_type="analysis_failed",
        )
        case_snapshot = attach_last_report_action(case_id, fail_action)
        snapshot = build_domain_snapshot(case_id)
        body = build_error_response(
            reason,
            snapshot=snapshot,
            data={
                "case": case_snapshot,
                "latest_case": case_snapshot,
                "report_action": fail_action,
                "workbench_refresh": snapshot.get("workbench_refresh", {}),
            },
        )
        return body, 500
