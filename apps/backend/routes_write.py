import logging

from auth import get_or_create_user, requires_auth
from database import db
from flask import Blueprint, jsonify, request
from models import FileSystemItem, User
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

write_bp = Blueprint("write", __name__)


@write_bp.route("/filesystem", methods=["POST"])
@requires_auth
def create_filesystem_item():
    try:
        user = get_or_create_user(db, User)
        data = request.get_json()

        if not data or "name" not in data or "type" not in data:
            return jsonify({"error": "Name and type are required"}), 400

        if data["type"] not in ["folder", "file"]:
            return jsonify({"error": "Type must be either folder or file"}), 400

        existing_item = FileSystemItem.query.filter_by(
            name=data["name"], parent_id=data.get("parent_id"), owner_id=user.id
        ).first()

        if existing_item:
            return (
                jsonify({"error": "An item with this name already exists in this folder"}),
                400,
            )

        item = FileSystemItem(
            name=data["name"],
            type=data["type"],
            parent_id=data.get("parent_id"),
            owner_id=user.id,
            size=data.get("size"),
            mime_type=data.get("mime_type"),
            path=data.get("path"),
        )

        db.session.add(item)
        db.session.commit()

        logger.info("Created filesystem item: %s", item.name)
        return jsonify(item.to_dict()), 201

    except IntegrityError as e:
        db.session.rollback()
        logger.error("[ERROR] Integrity error creating filesystem item: %s", str(e))
        if "unique_name_per_location_per_owner" in str(e):
            return (
                jsonify({"error": "An item with this name already exists in this folder"}),
                409,
            )
        return jsonify({"error": "Database constraint violation"}), 409
    except Exception as e:
        db.session.rollback()
        logger.error("[ERROR] Error creating filesystem item: %s", str(e))
        return jsonify({"error": "Internal server error"}), 500


@write_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200
