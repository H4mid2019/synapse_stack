import logging
import os
from io import BytesIO

from flask import Blueprint, jsonify, request, send_file
from google.cloud import storage
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

try:
    import magic

    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

try:
    from PyPDF2 import PdfReader

    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

from auth import get_or_create_user, requires_auth
from database import db
from models import FileSystemItem, User

logger = logging.getLogger(__name__)

operations_bp = Blueprint("operations", __name__)

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

MAX_FILE_SIZE = 100 * 1024 * 1024
ALLOWED_EXTENSIONS = {"pdf"}
ALLOWED_MIME_TYPES = {"application/pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_pdf_content(file_content):
    if not file_content.startswith(b"%PDF-"):
        return False, "File is not a valid PDF (invalid header)"

    if HAS_MAGIC:
        mime = magic.from_buffer(file_content[:2048], mime=True)
        if mime != "application/pdf":
            return False, f"File MIME type is {mime}, expected application/pdf"

    if HAS_PYPDF2:
        try:
            pdf_file = BytesIO(file_content)
            reader = PdfReader(pdf_file)
            page_count = len(reader.pages)
            if page_count == 0:
                return False, "PDF file appears to be empty or corrupted"
        except Exception as e:
            return False, f"PDF validation failed: {str(e)}"

    return True, "Valid PDF file"


def validate_file_size(file_content):
    size = len(file_content)
    if size > MAX_FILE_SIZE:
        size_mb = size / (1024 * 1024)
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        return False, f"File too large: {size_mb:.1f}MB (max {max_mb}MB)"
    return True, "File size OK"


TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
USE_GCS = GCS_BUCKET_NAME is not None

if USE_GCS:
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        logger.info("Google Cloud Storage initialized: %s", GCS_BUCKET_NAME)
    except Exception as e:
        logger.error("Failed to initialize GCS: %s", str(e))
        USE_GCS = False
        logger.info("Falling back to local file storage")
else:
    logger.info("Using local file storage (GCS_BUCKET_NAME not set)")


def get_file_path(item_id, filename=None):
    if filename and "." in filename:
        extension = filename.rsplit(".", 1)[1]
        base_path = (
            f"uploads/{item_id}.{extension}" if USE_GCS else os.path.join(UPLOAD_FOLDER, f"{item_id}.{extension}")
        )
    else:
        base_path = f"uploads/{item_id}" if USE_GCS else os.path.join(UPLOAD_FOLDER, str(item_id))
    return base_path


@operations_bp.route("/filesystem/<int:item_id>", methods=["PUT"])
@requires_auth
def update_filesystem_item(item_id):
    try:
        user = get_or_create_user(db, User)
        item = FileSystemItem.query.filter_by(id=item_id, owner_id=user.id).first()

        if not item:
            return jsonify({"error": "Item not found"}), 404

        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        if "name" in data:
            existing_item = FileSystemItem.query.filter(
                FileSystemItem.name == data["name"],
                FileSystemItem.parent_id == item.parent_id,
                FileSystemItem.owner_id == user.id,
                FileSystemItem.id != item_id,
            ).first()

            if existing_item:
                return (
                    jsonify({"error": "An item with this name already exists in this folder"}),
                    400,
                )

            item.name = data["name"]

        if "parent_id" in data:
            item.parent_id = data["parent_id"]

        db.session.commit()

        logger.info("Updated filesystem item: %s", item.name)
        return jsonify(item.to_dict()), 200

    except IntegrityError as e:
        db.session.rollback()
        logger.error("Integrity error updating filesystem item %s: %s", item_id, str(e))
        if "unique_name_per_location_per_owner" in str(e):
            return (
                jsonify({"error": "An item with this name already exists in this folder"}),
                409,
            )
        return jsonify({"error": "Database constraint violation"}), 409
    except Exception as e:
        db.session.rollback()
        logger.error("Error updating filesystem item %s: %s", item_id, str(e))
        return jsonify({"error": "Internal server error"}), 500


@operations_bp.route("/filesystem/<int:item_id>", methods=["DELETE"])
@requires_auth
def delete_filesystem_item(item_id):
    try:
        user = get_or_create_user(db, User)
        item = FileSystemItem.query.filter_by(id=item_id, owner_id=user.id).first()

        if not item:
            return jsonify({"error": "Item not found"}), 404

        if item.type == "file":
            file_path = get_file_path(item_id, item.name)
            if USE_GCS:
                blob = bucket.blob(file_path)
                if blob.exists():
                    blob.delete()
                    logger.info("Deleted file from GCS: %s", file_path)
                else:
                    logger.warning("File not found in GCS: %s", file_path)
            else:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info("Deleted file from local storage: %s", file_path)
                else:
                    logger.warning("File not found on disk: %s", file_path)

        if item.type == "folder":

            def delete_children(parent_id):
                children = FileSystemItem.query.filter_by(parent_id=parent_id).all()
                for child in children:
                    if child.type == "file":
                        file_path = get_file_path(child.id, child.name)
                        if USE_GCS:
                            blob = bucket.blob(file_path)
                            if blob.exists():
                                blob.delete()
                                logger.info("Deleted child file from GCS: %s", file_path)
                            else:
                                logger.warning("Child file not found in GCS: %s", file_path)
                        else:
                            if os.path.exists(file_path):
                                os.remove(file_path)
                                logger.info("Deleted child file from local storage: %s", file_path)
                            else:
                                logger.warning("Child file not found on disk: %s", file_path)
                    elif child.type == "folder":
                        delete_children(child.id)
                    db.session.delete(child)

            delete_children(item.id)

        db.session.delete(item)
        db.session.commit()

        logger.info("Deleted filesystem item: %s", item.name)
        return jsonify({"message": "Item deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        logger.error("Error deleting filesystem item %s: %s", item_id, str(e))
        return jsonify({"error": "Internal server error"}), 500


@operations_bp.route("/filesystem/upload", methods=["POST"])
@requires_auth
def upload_file():
    try:
        user = get_or_create_user(db, User)

        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Validate file extension
        if not allowed_file(file.filename):
            return jsonify({"error": "Only PDF files are allowed"}), 400

        parent_id = request.form.get("parent_id", type=int)
        filename = secure_filename(file.filename)

        if not filename.lower().endswith(".pdf"):
            filename = filename + ".pdf" if filename else "document.pdf"

        existing_item = FileSystemItem.query.filter_by(name=filename, parent_id=parent_id, owner_id=user.id).first()

        if existing_item:
            return (
                jsonify({"error": "A file with this name already exists in this folder"}),
                400,
            )

        file_content = file.read()

        size_valid, size_message = validate_file_size(file_content)
        if not size_valid:
            return jsonify({"error": size_message}), 400

        pdf_valid, pdf_message = validate_pdf_content(file_content)
        if not pdf_valid:
            return jsonify({"error": pdf_message}), 400

        file_size = len(file_content)

        item = FileSystemItem(
            name=filename,
            type="file",
            parent_id=parent_id,
            owner_id=user.id,
            size=file_size,
            mime_type="application/pdf",
        )

        db.session.add(item)
        db.session.flush()

        file_path = get_file_path(item.id, filename)

        if USE_GCS:
            blob = bucket.blob(file_path)
            blob.upload_from_string(file_content, content_type=item.mime_type)
            logger.info("Uploaded file to GCS: %s", file_path)
        else:
            with open(file_path, "wb") as f:
                f.write(file_content)
            logger.info("Uploaded file to local storage: %s", file_path)

        item.path = file_path
        db.session.commit()

        try:
            import requests

            logger.info("Attempting to notify text extractor for file %s", item.id)
            extraction_response = requests.post(
                "http://localhost:6004/extract",
                json={"file_id": item.id, "file_path": file_path},
                timeout=5,
            )
            logger.info("Extractor response status: %s", extraction_response.status_code)
            logger.info("Extractor response body: %s", extraction_response.text)

            if extraction_response.status_code == 200:
                logger.info("File %s queued for text extraction", item.id)
            else:
                logger.warning("Failed to queue file %s for extraction: %s", item.id, extraction_response.status_code)
        except requests.exceptions.RequestException as e:
            logger.error("Network error contacting text extractor: %s", str(e))
        except Exception as e:
            logger.error("Unexpected error notifying text extractor: %s", str(e))

        logger.info("Uploaded file: %s", item.name)
        return jsonify(item.to_dict()), 201

    except IntegrityError as e:
        db.session.rollback()
        logger.error("Integrity error uploading file: %s", str(e))
        if "unique_name_per_location_per_owner" in str(e):
            return (
                jsonify({"error": "A file with this name already exists in this folder"}),
                409,
            )
        return jsonify({"error": "Database constraint violation"}), 409
    except Exception as e:
        db.session.rollback()
        logger.error("Error uploading file: %s", str(e))
        return jsonify({"error": "Internal server error"}), 500


@operations_bp.route("/filesystem/<int:item_id>/download", methods=["GET"])
@requires_auth
def download_file(item_id):
    try:
        user = get_or_create_user(db, User)
        item = FileSystemItem.query.filter_by(id=item_id, owner_id=user.id).first()

        if not item:
            return jsonify({"error": "Item not found"}), 404

        if item.type != "file":
            return jsonify({"error": "Item is not a file"}), 400

        file_path = get_file_path(item_id, item.name)

        if USE_GCS:
            blob = bucket.blob(file_path)
            if not blob.exists():
                return jsonify({"error": "File not found in GCS"}), 404

            file_data = blob.download_as_bytes()
            return send_file(
                BytesIO(file_data),
                as_attachment=True,
                download_name=item.name,
                mimetype=item.mime_type,
            )
        else:
            if not os.path.exists(file_path):
                return jsonify({"error": "File not found on disk"}), 404

            return send_file(file_path, as_attachment=True, download_name=item.name)

    except Exception as e:
        logger.error("Error downloading file %s: %s", item_id, str(e))
        return jsonify({"error": "Internal server error"}), 500


@operations_bp.route("/filesystem/search", methods=["GET"])
@requires_auth
def search_files():
    try:
        user = get_or_create_user(db, User)

        query = request.args.get("q", "").strip()
        file_type = request.args.get("type", "").strip()
        parent_id = request.args.get("parent_id", type=int)
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 50, type=int)

        if not query:
            return jsonify({"error": "Search query is required"}), 400

        if limit > 100:
            limit = 100

        if page < 1:
            page = 1

        base_query = FileSystemItem.query.filter_by(owner_id=user.id)

        from sqlalchemy import or_

        search_conditions = [FileSystemItem.name.ilike(f"%{query}%")]

        search_conditions.append(FileSystemItem.content_text.ilike(f"%{query}%"))

        base_query = base_query.filter(or_(*search_conditions))

        if file_type in ["file", "folder"]:
            base_query = base_query.filter(FileSystemItem.type == file_type)

        def get_folder_ids_recursive(folder_id):
            folder_ids = [folder_id]
            subfolders = FileSystemItem.query.filter_by(parent_id=folder_id, type="folder", owner_id=user.id).all()

            for subfolder in subfolders:
                folder_ids.extend(get_folder_ids_recursive(subfolder.id))

            return folder_ids

        if parent_id is not None:
            parent_folder = FileSystemItem.query.filter_by(id=parent_id, owner_id=user.id, type="folder").first()
            if not parent_folder:
                return jsonify({"error": "Parent folder not found"}), 404

            searchable_folder_ids = get_folder_ids_recursive(parent_id)
            base_query = base_query.filter(FileSystemItem.parent_id.in_(searchable_folder_ids))
        else:
            all_folders = FileSystemItem.query.filter_by(owner_id=user.id, type="folder").all()

            searchable_folder_ids = [None]
            for folder in all_folders:
                searchable_folder_ids.append(folder.id)

        base_query = base_query.order_by(FileSystemItem.name.asc())

        total_count = base_query.count()

        offset = (page - 1) * limit
        items = base_query.offset(offset).limit(limit).all()

        total_pages = (total_count + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1

        results = [item.to_dict() for item in items]

        logger.info(
            "Search completed: query='%s', type='%s', parent_id=%s, found %d items",
            query,
            file_type,
            parent_id,
            len(results),
        )

        return (
            jsonify(
                {
                    "results": results,
                    "pagination": {
                        "current_page": page,
                        "total_pages": total_pages,
                        "total_items": total_count,
                        "items_per_page": limit,
                        "has_next": has_next,
                        "has_prev": has_prev,
                    },
                    "query": query,
                    "filters": {
                        "type": file_type if file_type else None,
                        "parent_id": parent_id,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error("Error searching files: %s", str(e))
        return jsonify({"error": "Internal server error"}), 500


@operations_bp.route("/filesystem/<int:item_id>/extract", methods=["POST"])
@requires_auth
def trigger_text_extraction(item_id):
    try:
        user = get_or_create_user(db, User)
        item = FileSystemItem.query.filter_by(id=item_id, owner_id=user.id).first()

        if not item:
            return jsonify({"error": "Item not found"}), 404

        if item.type != "file":
            return jsonify({"error": "Item is not a file"}), 400

        item.content_extracted = False
        item.extraction_error = None
        item.content_text = None
        db.session.commit()

        try:
            import requests

            extraction_response = requests.post(
                "http://localhost:6004/extract", json={"file_id": item.id, "file_path": item.path}, timeout=1
            )
            if extraction_response.status_code == 200:
                logger.info("File %s queued for text extraction", item.id)
                return jsonify({"message": "Text extraction queued", "file_id": item.id}), 200
            else:
                return (
                    jsonify({"error": "Failed to queue extraction", "status_code": extraction_response.status_code}),
                    502,
                )
        except Exception as e:
            logger.error("Could not notify text extractor: %s", str(e))
            return jsonify({"error": "Text extraction service unavailable"}), 503

    except Exception as e:
        logger.error("Error triggering extraction for %s: %s", item_id, str(e))
        return jsonify({"error": "Internal server error"}), 500


@operations_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200


if TEST_MODE:

    @operations_bp.route("/test/reset-database", methods=["POST"])
    def reset_database():
        try:
            logger.info("Resetting database for tests...")

            db.drop_all()
            logger.info("Dropped all tables")

            db.create_all()
            logger.info("Created all tables")

            test_user = User(auth0_id="test|12345", email="test@example.com", name="Test User")
            db.session.add(test_user)
            db.session.commit()
            logger.info("Created test user (ID: %d)", test_user.id)

            return (
                jsonify(
                    {
                        "message": "Database reset successful",
                        "test_user_id": test_user.id,
                    }
                ),
                200,
            )

        except Exception as e:
            logger.error("Error resetting database: %s", str(e))
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @operations_bp.route("/test/cleanup-database", methods=["POST"])
    def cleanup_database():
        try:
            logger.info("Cleaning up test database...")

            FileSystemItem.query.delete()
            logger.info("Deleted all filesystem items")

            User.query.filter(User.auth0_id != "test|12345").delete()
            logger.info("Deleted non-test users")

            db.session.commit()

            return jsonify({"message": "Database cleanup successful"}), 200

        except Exception as e:
            logger.error("Error cleaning database: %s", str(e))
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
