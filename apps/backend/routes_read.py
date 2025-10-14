import logging

from flask import Blueprint, jsonify, request
from sqlalchemy import text

from auth import get_or_create_user, requires_auth
from database import db
from models import FileSystemItem, User

logger = logging.getLogger(__name__)

read_bp = Blueprint("read", __name__)


@read_bp.route("/filesystem", methods=["GET"])
@requires_auth
def get_filesystem_items():
    try:
        user = get_or_create_user(db, User)
        parent_id = request.args.get("parent_id", default=None, type=int)

        if parent_id is None:
            items = FileSystemItem.query.filter_by(
                parent_id=None, owner_id=user.id
            ).all()
            return (
                jsonify(
                    {"items": [item.to_dict() for item in items], "breadcrumb": []}
                ),
                200,
            )
        else:
            items = FileSystemItem.query.filter_by(
                parent_id=parent_id, owner_id=user.id
            ).all()

            # Get breadcrumb using single recursive CTE query
            query = text(
                """
                WITH RECURSIVE breadcrumb_path AS (
                    SELECT id, name, type, parent_id, created_at,
                           updated_at, owner_id, size, mime_type, path,
                           0 as depth
                    FROM filesystem_items
                    WHERE id = :item_id AND owner_id = :owner_id

                    UNION ALL

                    SELECT f.id, f.name, f.type, f.parent_id,
                           f.created_at, f.updated_at, f.owner_id,
                           f.size, f.mime_type, f.path, bp.depth + 1
                    FROM filesystem_items f
                    INNER JOIN breadcrumb_path bp ON f.id = bp.parent_id
                    WHERE f.owner_id = :owner_id
                )
                SELECT id, name, type, parent_id, created_at,
                       updated_at, owner_id, size, mime_type, path
                FROM breadcrumb_path
                ORDER BY depth DESC
            """
            )

            result = db.session.execute(
                query, {"item_id": parent_id, "owner_id": user.id}
            )
            rows = result.fetchall()

            breadcrumb = []
            for row in rows:
                breadcrumb.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "type": row[2],
                        "parent_id": row[3],
                        "created_at": row[4].isoformat() if row[4] else None,
                        "updated_at": row[5].isoformat() if row[5] else None,
                        "owner_id": row[6],
                        "size": row[7],
                        "mime_type": row[8],
                        "path": row[9],
                    }
                )

            return (
                jsonify(
                    {
                        "items": [item.to_dict() for item in items],
                        "breadcrumb": breadcrumb,
                    }
                ),
                200,
            )

    except Exception as e:
        logger.error("[ERROR] Error fetching filesystem items: %s", str(e))
        return jsonify({"error": "Internal server error"}), 500


@read_bp.route("/filesystem/<int:item_id>", methods=["GET"])
@requires_auth
def get_filesystem_item(item_id):
    try:
        user = get_or_create_user(db, User)
        item = FileSystemItem.query.filter_by(id=item_id, owner_id=user.id).first()

        if not item:
            return jsonify({"error": "Item not found"}), 404

        return jsonify(item.to_dict()), 200

    except Exception as e:
        logger.error("[ERROR] Error fetching filesystem item %s: %s", item_id, str(e))
        return jsonify({"error": "Internal server error"}), 500
