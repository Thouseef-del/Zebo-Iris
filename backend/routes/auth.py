# backend/routes/auth.py

import jwt
import datetime
from flask import Blueprint, request, jsonify
from config import Config

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """
    Simple PIN-based role login.

    Accepts JSON: { "role": "admin" | "doctor", "pin": "1234" }
    Returns a JWT token with the role claim.
    """
    data = request.json or {}
    role = data.get("role", "").lower()
    pin = data.get("pin", "")

    if role not in ("admin", "doctor"):
        return jsonify({"status": "Error", "message": "Invalid role"}), 400

    expected_pin = Config.ADMIN_PIN if role == "admin" else Config.DOCTOR_PIN

    if pin != expected_pin:
        return jsonify({"status": "Error", "message": "Invalid PIN"}), 401

    token = jwt.encode(
        {
            "role": role,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8),
        },
        Config.JWT_SECRET,
        algorithm="HS256",
    )

    return jsonify({
        "status": "Success",
        "token": token,
        "role": role,
    })


@auth_bp.route("/auth/verify", methods=["GET"])
def verify_token():
    """Verify the current JWT token and return the role."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"status": "Error", "message": "No token provided"}), 401

    token = auth_header.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        return jsonify({"status": "Success", "role": payload["role"]})
    except jwt.ExpiredSignatureError:
        return jsonify({"status": "Error", "message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"status": "Error", "message": "Invalid token"}), 401
