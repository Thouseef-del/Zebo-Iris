# backend/routes/admin.py

from flask import Blueprint, jsonify, request
from models.user_model import UserModel
from database.db_connection import db

admin_bp = Blueprint("admin", __name__)

user_model = UserModel(db)


@admin_bp.route("/users", methods=["GET"])
def get_all_users():
    """Return all registered users (without iris codes)."""
    try:
        users = user_model.get_all_users()

        formatted_users = []
        for user in users:
            formatted_users.append({
                "id": str(user.get("_id")),
                "name": user.get("name"),
                "address": user.get("address"),
                "phone_no": user.get("phone_no"),
                "relationship": user.get("relationship"),
                "registered_at": str(user.get("created_at", "")),
            })

        return jsonify({
            "status": "Success",
            "total_users": len(formatted_users),
            "data": formatted_users,
        })

    except Exception as e:
        return jsonify({
            "status": "Error",
            "message": f"Failed to fetch users: {str(e)}"
        }), 500


@admin_bp.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    """Return a single user by their MongoDB ObjectId."""
    try:
        user = user_model.get_user_by_id(user_id)
        if user is None:
            return jsonify({"status": "Error", "message": "User not found"}), 404

        return jsonify({"status": "Success", "data": user})

    except Exception as e:
        return jsonify({
            "status": "Error",
            "message": f"Invalid user ID: {str(e)}"
        }), 400


@admin_bp.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    """Delete a user by their MongoDB ObjectId."""
    try:
        deleted = user_model.delete_user(user_id)
        if not deleted:
            return jsonify({"status": "Error", "message": "User not found"}), 404

        return jsonify({"status": "Success", "message": "User deleted successfully"})

    except Exception as e:
        return jsonify({
            "status": "Error",
            "message": f"Delete failed: {str(e)}"
        }), 400


@admin_bp.route("/stats", methods=["GET"])
def get_stats():
    """Return basic system statistics."""
    try:
        total = user_model.count_users()
        return jsonify({
            "status": "Success",
            "total_registered_users": total,
        })

    except Exception as e:
        return jsonify({
            "status": "Error",
            "message": f"Stats failed: {str(e)}"
        }), 500