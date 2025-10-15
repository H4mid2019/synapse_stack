"""
Local development reverse proxy
Routes requests to appropriate backend app based on HTTP method and path
"""

import logging

import requests
from flask import Flask, Response, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Backend service URLs
READ_SERVICE = "http://localhost:6001"
WRITE_SERVICE = "http://localhost:6002"
OPERATIONS_SERVICE = "http://localhost:6003"


def proxy_request(target_url):
    """Forward request to target service"""
    url = f"{target_url}{request.path}"

    headers = {key: value for key, value in request.headers if key.lower() != "host"}

    try:
        if request.method == "GET":
            resp = requests.get(url, params=request.args, headers=headers, stream=True)
        elif request.method == "POST":
            resp = requests.post(
                url,
                data=request.get_data(),
                headers=headers,
                params=request.args,
                stream=True,
            )
        elif request.method == "PUT":
            resp = requests.put(url, data=request.get_data(), headers=headers, params=request.args)
        elif request.method == "DELETE":
            resp = requests.delete(url, headers=headers, params=request.args)
        else:
            return Response("Method not allowed", status=405)

        excluded_headers = [
            "content-encoding",
            "content-length",
            "transfer-encoding",
            "connection",
        ]
        headers = [(name, value) for name, value in resp.raw.headers.items() if name.lower() not in excluded_headers]

        return Response(resp.content, resp.status_code, headers)

    except requests.exceptions.ConnectionError:
        logger.error("Connection failed to %s", target_url)
        return Response(f"Service unavailable: {target_url}", status=503)
    except Exception as e:
        logger.error("Proxy error: %s", str(e))
        return Response(f"Proxy error: {str(e)}", status=500)


@app.route("/api/health", methods=["GET"])
def health():
    """Health check - route to operations"""
    logger.info("[PROXY] Health check -> OPERATIONS")
    return proxy_request(OPERATIONS_SERVICE)


@app.route("/api/filesystem", methods=["GET", "POST"])
def filesystem_base():
    """Route GET to read, POST to write"""
    if request.method == "GET":
        logger.info("[PROXY] GET /api/filesystem -> READ")
        return proxy_request(READ_SERVICE)
    elif request.method == "POST":
        logger.info("[PROXY] POST /api/filesystem -> WRITE")
        return proxy_request(WRITE_SERVICE)


@app.route("/api/filesystem/<int:item_id>", methods=["GET", "PUT", "DELETE"])
def filesystem_item(item_id):
    """Route by method"""
    if request.method == "GET":
        logger.info("[PROXY] GET /api/filesystem/%s -> READ", item_id)
        return proxy_request(READ_SERVICE)
    elif request.method == "PUT":
        logger.info("[PROXY] PUT /api/filesystem/%s -> OPERATIONS", item_id)
        return proxy_request(OPERATIONS_SERVICE)
    elif request.method == "DELETE":
        logger.info("[PROXY] DELETE /api/filesystem/%s -> OPERATIONS", item_id)
        return proxy_request(OPERATIONS_SERVICE)


@app.route("/api/filesystem/upload", methods=["POST"])
def upload():
    """Upload to operations"""
    logger.info("[PROXY] POST /api/filesystem/upload -> OPERATIONS")
    return proxy_request(OPERATIONS_SERVICE)


@app.route("/api/filesystem/<int:item_id>/download", methods=["GET"])
def download(item_id):
    """Download from operations"""
    logger.info("[PROXY] GET /api/filesystem/%s/download -> OPERATIONS", item_id)
    return proxy_request(OPERATIONS_SERVICE)


@app.route("/api/filesystem/search", methods=["GET"])
def search():
    """Search files - route to operations"""
    logger.info("[PROXY] GET /api/filesystem/search -> OPERATIONS")
    return proxy_request(OPERATIONS_SERVICE)


@app.route("/api/test/<path:subpath>", methods=["POST"])
def test_endpoints(subpath):
    """Test endpoints to operations"""
    logger.info("[PROXY] POST /api/test/%s -> OPERATIONS", subpath)
    return proxy_request(OPERATIONS_SERVICE)


if __name__ == "__main__":
    print("Local development reverse proxy")
    print("-" * 40)
    print(f"READ:       {READ_SERVICE}")
    print(f"WRITE:      {WRITE_SERVICE}")
    print(f"OPERATIONS: {OPERATIONS_SERVICE}")
    print("Proxy:      http://localhost:5000")
    print("-" * 40)
    app.run(host="0.0.0.0", port=5000, debug=True)
