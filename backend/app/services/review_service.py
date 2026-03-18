from typing import Any, Dict, Tuple

from ..algorithms.review_decision import build_review_outcome
from ..repositories.case_repository import apply_review, attach_last_report_action
from ..repositories.dispute_repository import update_dispute_from_review
from ..repositories.report_repository import append_report_action
from ..repositories.review_repository import count_reviews, create_review, list_reviews
from ..schemas.contracts import ReviewSubmitRequest, build_error_response, build_success_response
from .domain_snapshot_service import build_domain_snapshot


def handle_reviews(raw_request: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    method = str(raw_request.get("method", "GET") or "GET").upper()

    if method == "GET":
        reviews = list_reviews()
        snapshot = build_domain_snapshot(raw_request.get("case_id", ""))
        selected_case_id = str(raw_request.get("case_id", "") or "")
        latest_case = None
        for item in snapshot.get("cases", []):
            if selected_case_id and item.get("id") == selected_case_id:
                latest_case = item
                break
        if latest_case is None:
            latest_case = (snapshot.get("cases") or [None])[0]
        body = build_success_response(
            data={
                "reviews": reviews,
                "count": len(reviews),
                "latest_case": latest_case,
                "workbench_refresh": snapshot.get("workbench_refresh", {}),
            },
            snapshot=snapshot,
            message="复核数据加载成功",
        )
        return body, 200

    if method != "POST":
        body = build_error_response("不支持的请求方法")
        return body, 405

    try:
        review_request = ReviewSubmitRequest.from_payload(raw_request.get("json") or {})
    except ValueError as exc:
        body = build_error_response(str(exc))
        return body, 400

    review_item = create_review(
        {
            "case_id": review_request.case_id,
            "reviewer": review_request.reviewer,
            "corrected_label": review_request.corrected_label,
            "corrected_area_mu": review_request.corrected_area_mu,
            "comment": review_request.comment,
            "requires_resurvey": review_request.requires_resurvey,
        }
    )

    dispute_item = update_dispute_from_review(
        case_id=review_request.case_id,
        reviewer=review_request.reviewer,
        requires_resurvey=review_request.requires_resurvey,
        comment=review_request.comment,
    )

    case_snapshot = apply_review(
        case_id=review_request.case_id,
        review_item=review_item,
        dispute_status=dispute_item.get("status", "无"),
    )

    review_outcome = build_review_outcome(review_item)
    action_title = "复核退回" if review_request.requires_resurvey else "复核结案"
    action_detail = review_request.comment or review_outcome.get("summary", "")

    report_action = append_report_action(
        case_id=review_request.case_id,
        case_status=case_snapshot.get("status", ""),
        operator=review_request.reviewer,
        title=action_title,
        detail=action_detail,
        action_type="review",
    )
    case_snapshot = attach_last_report_action(review_request.case_id, report_action)

    snapshot = build_domain_snapshot(review_request.case_id)
    body = build_success_response(
        data={
            "review": review_item,
            "count": count_reviews(),
            "case": case_snapshot,
            "latest_case": case_snapshot,
            "review_outcome": review_outcome,
            "dispute": dispute_item,
            "dispute_status": dispute_item.get("status", "无"),
            "review_label": review_item.get("corrected_label", ""),
            "corrected_area_mu": review_item.get("corrected_area_mu", ""),
            "reviewer": review_item.get("reviewer", "系统用户"),
            "report_action": report_action,
            "workbench_refresh": snapshot.get("workbench_refresh", {}),
        },
        snapshot=snapshot,
        message="复核提交成功",
    )
    return body, 200
