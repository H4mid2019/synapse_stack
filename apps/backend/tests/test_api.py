import json


class TestFileSystemAPI:

    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["status"] == "healthy"

    def test_get_root_items_empty(self, client):
        response = client.get("/api/filesystem")
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert "items" in response_data
        assert isinstance(response_data["items"], list)

    def test_get_root_items_with_data(self, client, sample_item):  # noqa: ARG002
        response = client.get("/api/filesystem")
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert "items" in response_data
        assert len(response_data["items"]) >= 1
        assert any(item["name"] == "Test Folder" for item in response_data["items"])

    def test_get_item_by_id(self, client, sample_item):
        response = client.get(f"/api/filesystem/{sample_item.id}")
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["name"] == "Test Folder"
        assert response_data["type"] == "folder"
        assert response_data["id"] == str(sample_item.id)  # ID returned as string now

    def test_get_item_not_found(self, client):
        response = client.get("/api/filesystem/999999")
        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert "error" in response_data

    def test_create_folder(self, client):
        data = {"name": "New Folder", "type": "folder", "parent_id": None}
        response = client.post(
            "/api/filesystem", data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data["name"] == "New Folder"
        assert response_data["type"] == "folder"
        assert "id" in response_data

    def test_create_item_missing_name(self, client):
        data = {"type": "folder"}
        response = client.post(
            "/api/filesystem", data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert "error" in response_data

    def test_update_item(self, client, sample_item):
        data = {"name": "Updated Folder"}
        response = client.put(
            f"/api/filesystem/{sample_item.id}",
            data=json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["name"] == "Updated Folder"

    def test_update_item_not_found(self, client):
        data = {"name": "Updated Folder"}
        response = client.put(
            "/api/filesystem/999999",
            data=json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == 404

    def test_delete_item(self, client, sample_item):
        response = client.delete(f"/api/filesystem/{sample_item.id}")
        assert response.status_code == 200

        get_response = client.get(f"/api/filesystem/{sample_item.id}")
        assert get_response.status_code == 404

    def test_delete_item_not_found(self, client):
        response = client.delete("/api/filesystem/999999")
        assert response.status_code == 404
