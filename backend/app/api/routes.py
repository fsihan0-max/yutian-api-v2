from flask import Blueprint, jsonify, request

from ..services.analysis_service import handle_analyze
from ..services.health_service import get_health_response
from ..services.review_service import handle_reviews
from ..services.sample_service import handle_samples

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/health")
def health():
    return get_health_response()


@api_bp.route("/samples", methods=["GET", "POST"])
def samples():
    return handle_samples()


@api_bp.route("/reviews", methods=["GET", "POST"])
def reviews():
    payload = {
        "method": request.method,
        "json": request.get_json(silent=True),
        "case_id": request.args.get("case_id", ""),
    }
    body, status = handle_reviews(payload)
    return jsonify(body), status


@api_bp.route("/analyze", methods=["POST"])
def analyze():
    content_type = str(request.content_type or "")
    is_multipart = "multipart/form-data" in content_type
    upload = request.files.get("file") if is_multipart else None

    payload = {
        "content_type": content_type,
        "json": None if is_multipart else (request.get_json(silent=True) or {}),
        "form": request.form.to_dict() if is_multipart else {},
        "file_bytes": upload.read() if upload else None,
        "file_name": upload.filename if upload else "",
    }
    body, status = handle_analyze(payload)
    return jsonify(body), status
