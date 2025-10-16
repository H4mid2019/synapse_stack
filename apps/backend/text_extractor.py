import logging
import os
import queue
import threading
from io import BytesIO

from database import db
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from google.cloud import storage
from models import FileSystemItem
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

try:
    from PyPDF2 import PdfReader

    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

logger = logging.getLogger(__name__)

EXTRACTOR_PORT = 6004
EXTRACTOR_HOST = "0.0.0.0"

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
USE_GCS = GCS_BUCKET_NAME is not None
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")

if USE_GCS:
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        logger.info("Text Extractor: GCS initialized")
    except Exception as e:
        logger.error("Text Extractor: Failed to initialize GCS: %s", str(e))
        USE_GCS = False


def get_file_path(item_id):
    if USE_GCS:
        return f"uploads/{item_id}"
    return os.path.join(UPLOAD_FOLDER, str(item_id))


class TextExtractionQueue:

    def __init__(self, app=None):
        self.queue = queue.Queue()
        self.running = False
        self.worker_thread = None
        self.app = app

    def start(self):
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
            logger.info("Text extraction worker started")

    def stop(self):
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
            logger.info("Text extraction worker stopped")

    def add_job(self, file_id, file_path=None):
        try:
            self.queue.put({"file_id": file_id, "file_path": file_path}, timeout=1)
            logger.info("Added file %s to extraction queue", file_id)
            return True
        except queue.Full:
            logger.error("Extraction queue is full, dropping file %s", file_id)
            return False

    def _get_file_content(self, file_id, file_path=None, filename=None):
        if file_path is None:
            if filename and "." in filename:
                extension = filename.rsplit(".", 1)[1]
                if USE_GCS:
                    file_path = f"uploads/{file_id}.{extension}"
                else:
                    file_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.{extension}")
            else:
                if USE_GCS:
                    file_path = f"uploads/{file_id}"
                else:
                    file_path = os.path.join(UPLOAD_FOLDER, str(file_id))

        try:
            if USE_GCS:
                blob = bucket.blob(file_path)
                if not blob.exists():
                    logger.error("File %s not found in GCS", file_path)
                    return None
                return blob.download_as_bytes()
            else:
                if not os.path.exists(file_path):
                    logger.error("File %s not found on disk", file_path)
                    return None
                with open(file_path, "rb") as f:
                    return f.read()
        except Exception as e:
            logger.error("Failed to read file %s: %s", file_path, str(e))
            return None

    def _extract_pdf_text(self, file_content):
        if not HAS_PYPDF2:
            return None, "PyPDF2 not available"

        try:
            pdf_file = BytesIO(file_content)
            reader = PdfReader(pdf_file)

            if len(reader.pages) == 0:
                return None, "PDF has no pages"

            text = ""
            pages_with_text = 0
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += f"Page {page_num + 1}:\n{page_text}\n\n"
                        pages_with_text += 1
                except Exception as e:
                    logger.warning("Failed to extract text from page %d: %s", page_num + 1, str(e))
                    continue

            text = text.strip()
            if not text:
                return None, f"No text content found in PDF ({len(reader.pages)} pages scanned)"

            logger.info("Extracted text from %d/%d pages", pages_with_text, len(reader.pages))
            return text, None
        except Exception as e:
            return None, f"PDF extraction failed: {str(e)}"

    def _worker(self):
        logger.info("Text extraction worker loop started")

        while self.running:
            try:
                job = self.queue.get(timeout=1)
                file_id = job["file_id"]
                file_path = job.get("file_path")

                logger.info("Processing file %s for text extraction", file_id)

                with self.app.app_context():
                    file_item = db.session.get(FileSystemItem, file_id)
                    if not file_item:
                        logger.error("File %s not found in database", file_id)
                        continue

                    if file_item.type != "file":
                        logger.warning("Item %s is not a file, skipping extraction", file_id)
                        continue

                    if file_item.content_extracted:
                        logger.info("File %s already has extracted content, skipping", file_id)
                        continue

                    file_content = self._get_file_content(file_id, file_path, file_item.name)
                    if not file_content:
                        self._update_extraction_status(file_id, False, "Failed to read file content")
                        continue

                    extracted_text = None
                    error_message = None

                    if file_item.mime_type == "application/pdf":
                        extracted_text, error_message = self._extract_pdf_text(file_content)
                    else:
                        error_message = f"Unsupported file type: {file_item.mime_type}"

                    self._update_extraction_status(file_id, extracted_text is not None, error_message, extracted_text)

                    if extracted_text:
                        logger.info("Extracted %d characters from file %s", len(extracted_text), file_id)
                    else:
                        logger.error("Failed to extract text from file %s: %s", file_id, error_message)

            except queue.Empty:
                continue
            except Exception as e:
                logger.error("Error in extraction worker: %s", str(e))
                continue

    def _update_extraction_status(self, file_id, success, error_message=None, content_text=None):
        try:
            with self.app.app_context():
                file_item = db.session.get(FileSystemItem, file_id)
                if file_item:
                    file_item.content_extracted = success
                    file_item.extraction_error = error_message
                    if content_text:
                        file_item.content_text = content_text
                    db.session.commit()
                    logger.info("Updated extraction status for file %s: success=%s", file_id, success)
        except SQLAlchemyError as e:
            logger.error("Database error updating file %s: %s", file_id, str(e))
            db.session.rollback()


extraction_queue = None


def init_extraction_queue(app):
    global extraction_queue
    extraction_queue = TextExtractionQueue(app)
    return extraction_queue


def notify_file_uploaded(file_id, file_path=None):
    if extraction_queue:
        return extraction_queue.add_job(file_id, file_path)
    return False


def start_extraction_service():
    if extraction_queue:
        extraction_queue.start()
        logger.info("Text extraction service started")


def stop_extraction_service():
    if extraction_queue:
        extraction_queue.stop()
        logger.info("Text extraction service stopped")


extraction_app = Flask(__name__)

database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/flask_react_db")

# CockroachDB URI conversion (same logic as app_factory.py)
if database_url.startswith("cockroachdb://"):
    database_url = database_url.replace("cockroachdb://", "cockroachdb+psycopg2://")
elif "cockroachlabs.cloud" in database_url or os.getenv("USE_COCKROACHDB", "").lower() == "true":
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "cockroachdb+psycopg2://")

extraction_app.config["SQLALCHEMY_DATABASE_URI"] = database_url
extraction_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

if "cockroachdb" in database_url:
    extraction_app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

db.init_app(extraction_app)


@extraction_app.route("/extract", methods=["POST"])
def extract_file():
    try:
        logger.info("Extract endpoint called")
        data = request.get_json()
        logger.info("Received data: %s", data)

        if not data or "file_id" not in data:
            logger.error("Missing file_id in request")
            return jsonify({"error": "file_id is required"}), 400

        file_id = data["file_id"]
        file_path = data.get("file_path")

        logger.info("Processing extraction request for file_id: %s, file_path: %s", file_id, file_path)

        success = notify_file_uploaded(file_id, file_path)
        if success:
            logger.info("File %s queued for extraction", file_id)
            return jsonify({"status": "queued", "file_id": file_id}), 200
        else:
            logger.error("Failed to queue file %s - queue is full", file_id)
            return jsonify({"error": "Queue is full"}), 503

    except Exception as e:
        logger.error("Error in extract endpoint: %s", str(e))
        return jsonify({"error": "Internal server error"}), 500


@extraction_app.route("/health", methods=["GET"])
def health_check():
    queue_size = extraction_queue.queue.qsize() if extraction_queue else 0
    return jsonify({"status": "healthy", "queue_size": queue_size}), 200


@extraction_app.route("/status/<int:file_id>", methods=["GET"])
def get_extraction_status(file_id):
    try:
        file_item = db.session.get(FileSystemItem, file_id)
        if not file_item:
            return jsonify({"error": "File not found"}), 404

        return (
            jsonify(
                {
                    "file_id": file_id,
                    "content_extracted": file_item.content_extracted,
                    "extraction_error": file_item.extraction_error,
                    "has_content": bool(file_item.content_text),
                    "file_name": file_item.name,
                    "file_path": file_item.path,
                    "mime_type": file_item.mime_type,
                    "size": file_item.size,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error("Error getting extraction status: %s", str(e))
        return jsonify({"error": "Internal server error"}), 500


@extraction_app.route("/test/extract/<int:file_id>", methods=["POST"])
def test_extract_file(file_id):
    try:
        file_item = db.session.get(FileSystemItem, file_id)
        if not file_item:
            return jsonify({"error": "File not found"}), 404

        if file_item.type != "file":
            return jsonify({"error": "Item is not a file"}), 400

        file_path = get_file_path(file_id)

        file_exists = False
        if USE_GCS:
            try:
                blob = bucket.blob(file_path)
                file_exists = blob.exists()
            except Exception as e:
                return (
                    jsonify(
                        {"error": "GCS access failed", "details": str(e), "file_path": file_path, "use_gcs": USE_GCS}
                    ),
                    500,
                )
        else:
            file_exists = os.path.exists(file_path)

        if not file_exists:
            return (
                jsonify(
                    {
                        "error": "File does not exist in storage",
                        "file_path": file_path,
                        "use_gcs": USE_GCS,
                        "gcs_bucket": GCS_BUCKET_NAME if USE_GCS else None,
                    }
                ),
                404,
            )

        try:
            if USE_GCS:
                blob = bucket.blob(file_path)
                file_content = blob.download_as_bytes()
            else:
                with open(file_path, "rb") as f:
                    file_content = f.read()
        except Exception as e:
            return jsonify({"error": "Failed to read file content", "details": str(e), "file_path": file_path}), 500

        if file_item.mime_type == "application/pdf":
            try:
                extracted_text, error_message = extraction_queue._extract_pdf_text(file_content)
                if extracted_text:
                    return (
                        jsonify(
                            {
                                "success": True,
                                "file_id": file_id,
                                "file_name": file_item.name,
                                "file_path": file_path,
                                "content_length": len(file_content),
                                "extracted_text_length": len(extracted_text),
                                "extracted_preview": (
                                    extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
                                ),
                                "storage_type": "GCS" if USE_GCS else "Local",
                            }
                        ),
                        200,
                    )
                else:
                    return (
                        jsonify(
                            {
                                "error": "PDF extraction failed",
                                "details": error_message,
                                "file_id": file_id,
                                "content_length": len(file_content),
                            }
                        ),
                        500,
                    )
            except Exception as e:
                return jsonify({"error": "PDF extraction exception", "details": str(e), "file_id": file_id}), 500
        else:
            return (
                jsonify(
                    {
                        "error": "Unsupported file type",
                        "mime_type": file_item.mime_type,
                        "supported_types": ["application/pdf"],
                    }
                ),
                400,
            )

    except Exception as e:
        logger.error("Error in test extraction: %s", str(e))
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@extraction_app.route("/test/files", methods=["GET"])
def list_files_for_testing():
    try:
        files = FileSystemItem.query.filter_by(type="file").all()
        file_list = []

        for file_item in files:
            file_path = get_file_path(file_item.id)

            if USE_GCS:
                try:
                    blob = bucket.blob(file_path)
                    exists = blob.exists()
                except Exception:
                    exists = False
            else:
                exists = os.path.exists(file_path)

            file_list.append(
                {
                    "id": file_item.id,
                    "name": file_item.name,
                    "mime_type": file_item.mime_type,
                    "size": file_item.size,
                    "content_extracted": file_item.content_extracted,
                    "extraction_error": file_item.extraction_error,
                    "file_exists": exists,
                    "file_path": file_path,
                }
            )

        return (
            jsonify(
                {
                    "files": file_list,
                    "total_files": len(file_list),
                    "storage_type": "GCS" if USE_GCS else "Local",
                    "gcs_bucket": GCS_BUCKET_NAME if USE_GCS else None,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error("Error listing files: %s", str(e))
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


if __name__ == "__main__":
    with extraction_app.app_context():
        init_extraction_queue(extraction_app)
        start_extraction_service()
        extraction_app.run(host=EXTRACTOR_HOST, port=EXTRACTOR_PORT, debug=False)
