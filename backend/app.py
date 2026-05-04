# backend/app.py

from flask import Flask
from flask_cors import CORS
from config import Config
from routes.register import register_bp
from routes.scan import scan_bp
from routes.admin import admin_bp
from routes.auth import auth_bp


def create_app():
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS for frontend dev server
    CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"])

    # Register blueprints
    app.register_blueprint(register_bp, url_prefix="/api")
    app.register_blueprint(scan_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api")

    # Health check
    @app.route("/")
    def index():
        return {"status": "running", "service": "Iris Recognition Emergency System"}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
