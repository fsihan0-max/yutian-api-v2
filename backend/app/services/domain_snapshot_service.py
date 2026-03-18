from typing import Any, Dict, List

from ..repositories.case_repository import list_cases
from ..repositories.dispute_repository import list_disputes
from ..repositories.report_repository import list_report_actions


def _build_workbench_refresh(cases: List[Dict[str, Any]], disputes: List[Dict[str, Any]]) -> Dict[str, Any]:
    pending_survey = sum(1 for item in cases if item.get("status") == "待查勘")
    analyzing = sum(1 for item in cases if item.get("status") == "分析中")
    pending_review = sum(1 for item in cases if item.get("status") == "待复核")
    closed = sum(1 for item in cases if item.get("status") == "已结案")
    open_disputes = sum(1 for item in disputes if item.get("status") != "已解决")
    high_risk = sum(1 for item in cases if float(item.get("riskScore") or 0) >= 0.7 and item.get("status") != "已结案")

    return {
        "case_total": len(cases),
        "pending_survey": pending_survey,
        "analyzing": analyzing,
        "pending_review": pending_review,
        "closed": closed,
        "open_disputes": open_disputes,
        "high_risk": high_risk,
    }


def _build_workbench_payload(refresh: Dict[str, Any], cases: List[Dict[str, Any]], disputes: List[Dict[str, Any]]) -> Dict[str, Any]:
    warnings = [
        {
            "title": f"争议案件 {item.get('title', item.get('caseId', ''))}",
            "detail": item.get("detail") or "",
        }
        for item in disputes
        if item.get("status") != "已解决"
    ][:4]

    return {
        "metrics": [
            {"label": "我的待办", "value": str(refresh["pending_survey"] + refresh["pending_review"] + refresh["analyzing"])},
            {"label": "待查勘", "value": str(refresh["pending_survey"])},
            {"label": "待复核", "value": str(refresh["pending_review"])},
            {"label": "异常预警", "value": str(refresh["open_disputes"] + refresh["high_risk"])},
        ],
        "todos": [
            {
                "title": item.get("id"),
                "detail": f"{item.get('town', '')}/{item.get('village', '')} {item.get('status', '')}",
            }
            for item in cases
            if item.get("status") != "已结案"
        ][:4],
        "warnings": warnings,
        "recentCases": sorted(cases, key=lambda item: str(item.get("updatedAt", "")), reverse=True)[:5],
        "quickActions": [
            {"text": "开始查勘", "route": "survey"},
            {"text": "待复核案件", "route": "cases"},
            {"text": "生成报告", "route": "reports"},
            {"text": "风险监管", "route": "risk"},
        ],
    }


def _build_risk_payload(cases: List[Dict[str, Any]], disputes: List[Dict[str, Any]]) -> Dict[str, Any]:
    town_map: Dict[str, float] = {}
    type_map: Dict[str, int] = {}
    for item in cases:
        town = item.get("town") or "未知乡镇"
        town_map[town] = town_map.get(town, 0.0) + float(item.get("recognizedAreaMu") or 0)
        disaster_type = item.get("disasterType") or "待判定"
        type_map[disaster_type] = type_map.get(disaster_type, 0) + 1

    town_distribution = [{"town": key, "area": round(value, 2)} for key, value in town_map.items()]
    town_distribution.sort(key=lambda item: item["area"], reverse=True)
    type_distribution = [{"label": key, "value": value} for key, value in type_map.items()]
    type_distribution.sort(key=lambda item: item["value"], reverse=True)

    high_risk_cases = [
        item
        for item in sorted(cases, key=lambda row: float(row.get("riskScore") or 0), reverse=True)
        if float(item.get("riskScore") or 0) >= 0.7 and item.get("status") != "已结案"
    ][:5]

    return {
        "metrics": [
            {"label": "待复核", "value": str(sum(1 for row in cases if row.get('status') == '待复核'))},
            {"label": "高风险", "value": str(len(high_risk_cases))},
            {"label": "争议案件", "value": str(sum(1 for row in disputes if row.get('status') != '已解决'))},
            {"label": "案件总量", "value": str(len(cases))},
        ],
        "townDistribution": town_distribution,
        "typeDistribution": type_distribution,
        "regionTrends": [
            {
                "title": "乡镇分布",
                "detail": "；".join([f"{row['town']} {row['area']}亩" for row in town_distribution]) or "暂无乡镇统计。",
            },
            {
                "title": "类型占比",
                "detail": "；".join([f"{row['label']} {row['value']}件" for row in type_distribution]) or "暂无类型统计。",
            },
        ],
        "dispatchTasks": [
            {
                "title": item.get("id"),
                "detail": f"{item.get('town', '')}/{item.get('village', '')} 风险分 {float(item.get('riskScore') or 0):.2f}，状态 {item.get('status', '')}",
            }
            for item in high_risk_cases
        ]
        or [{"title": "暂无高风险案件", "detail": "当前无紧急调度。"}],
    }


def build_domain_snapshot(selected_case_id: str = "") -> Dict[str, Any]:
    cases = list_cases()
    disputes = list_disputes()
    report_actions = list_report_actions(selected_case_id)
    workbench_refresh = _build_workbench_refresh(cases, disputes)

    return {
        "selected_case_id": selected_case_id,
        "cases": cases,
        "disputes": disputes,
        "report_actions": report_actions,
        "workbench_refresh": workbench_refresh,
        "workbench": _build_workbench_payload(workbench_refresh, cases, disputes),
        "risk": _build_risk_payload(cases, disputes),
    }
