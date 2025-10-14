import json


class TestItemAPI:

    def test_create_item(self, client):
        data = {"name": "New Item", "description": "New Description"}
        response = client.post(
            "/api/items", data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data["name"] == "New Item"
        assert response_data["description"] == "New Description"
        assert "id" in response_data

    def test_create_item_missing_name(self, client):
        data = {"description": "Description without name"}
        response = client.post(
            "/api/items", data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert "error" in response_data

    def test_get_items_empty(self, client):
        response = client.get("/api/items")
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data == []

    def test_get_items_with_data(self, client, sample_item):
        response = client.get("/api/items")
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert len(response_data) == 1
        assert response_data[0]["name"] == "Test Item"

    def test_get_item_by_id(self, client, sample_item):
        response = client.get(f"/api/items/{sample_item.id}")
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["name"] == "Test Item"
        assert response_data["id"] == sample_item.id

    def test_get_item_not_found(self, client):
        response = client.get("/api/items/999")
        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert "error" in response_data

    def test_update_item(self, client, sample_item):
        data = {"name": "Updated Item", "description": "Updated Description"}
        response = client.put(
            f"/api/items/{sample_item.id}",
            data=json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["name"] == "Updated Item"
        assert response_data["description"] == "Updated Description"

    def test_update_item_not_found(self, client):
        data = {"name": "Updated Item"}
        response = client.put(
            "/api/items/999", data=json.dumps(data), content_type="application/json"
        )

        assert response.status_code == 404

    def test_delete_item(self, client, sample_item):
        response = client.delete(f"/api/items/{sample_item.id}")
        assert response.status_code == 200

        # Verify item is deleted
        get_response = client.get(f"/api/items/{sample_item.id}")
        assert get_response.status_code == 404

    def test_delete_item_not_found(self, client):
        response = client.delete("/api/items/999")
        assert response.status_code == 404

    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["status"] == "healthy"
