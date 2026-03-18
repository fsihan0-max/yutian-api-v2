from flask import Flask
from flask_cors import CORS

from .api.routes import api_bp
from .repositories.json_repository import ensure_data_files


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    ensure_data_files()
    app.register_blueprint(api_bp)
    return app
