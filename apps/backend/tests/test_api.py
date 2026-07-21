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
        response = client.post("/api/filesystem", data=json.dumps(data), content_type="application/json")

        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data["name"] == "New_Folder"  # Sanitized name
        assert response_data["type"] == "folder"
        assert "id" in response_data

    def test_create_item_missing_name(self, client):
        data = {"type": "folder"}
        response = client.post("/api/filesystem", data=json.dumps(data), content_type="application/json")

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
        assert response_data["name"] == "Updated_Folder"  # Sanitized name

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

    def test_search_files_basic(self, client, sample_item):  # noqa: ARG002
        # Basic search test
        response = client.get("/api/filesystem/search?q=Test")
        assert response.status_code == 200

        response_data = json.loads(response.data)
        assert "results" in response_data
        assert "pagination" in response_data
        assert "query" in response_data
        assert response_data["query"] == "Test"

        # Should find the sample item
        assert len(response_data["results"]) >= 1
        found_item = next(
            (item for item in response_data["results"] if item["name"] == "Test Folder"),
            None,
        )
        assert found_item is not None

    def test_search_files_with_type_filter(self, client, sample_item):  # noqa: ARG002
        # Search with type filter
        response = client.get("/api/filesystem/search?q=Test&type=folder")
        assert response.status_code == 200

        response_data = json.loads(response.data)
        assert len(response_data["results"]) >= 1

        # All results should be folders
        for item in response_data["results"]:
            assert item["type"] == "folder"

    def test_search_files_no_query(self, client):
        # Search without query should return error
        response = client.get("/api/filesystem/search")
        assert response.status_code == 400

        response_data = json.loads(response.data)
        assert "error" in response_data
        assert "required" in response_data["error"].lower()

    def test_search_files_pagination(self, client, sample_item):  # noqa: ARG002
        # Test pagination
        response = client.get("/api/filesystem/search?q=Test&limit=1&page=1")
        assert response.status_code == 200

        response_data = json.loads(response.data)
        pagination = response_data["pagination"]

        assert "current_page" in pagination
        assert "total_pages" in pagination
        assert "total_items" in pagination
        assert "items_per_page" in pagination
        assert "has_next" in pagination
        assert "has_prev" in pagination

        assert pagination["current_page"] == 1
        assert pagination["items_per_page"] == 1

    def test_search_files_case_insensitive(self, client, sample_item):  # noqa: ARG002
        # Test case-insensitive search
        response = client.get("/api/filesystem/search?q=test")
        assert response.status_code == 200

        response_data = json.loads(response.data)
        # Should find the "Test Folder" item even with lowercase query
        found_item = next(
            (item for item in response_data["results"] if item["name"] == "Test Folder"),
            None,
        )
        assert found_item is not None


class TestAuthentication:
    """Requests without a valid credential must not reach any data."""

    def test_anonymous_request_is_rejected(self, anonymous_client):
        response = anonymous_client.get("/api/filesystem")
        assert response.status_code == 401

    def test_garbage_token_is_rejected(self, anonymous_client):
        response = anonymous_client.get("/api/filesystem", headers={"Authorization": "Bearer not-a-real-token"})
        assert response.status_code == 401

    def test_non_bearer_scheme_is_rejected(self, anonymous_client):
        response = anonymous_client.get("/api/filesystem", headers={"Authorization": "Basic dXNlcjpwYXNz"})
        assert response.status_code == 401

    def test_health_needs_no_credential(self, anonymous_client):
        """The load balancer has no token. Health must stay open."""
        assert anonymous_client.get("/api/health").status_code == 200


class TestAuthorization:
    """Authentication says who you are. These check what you may reach.

    The interesting failure is not the anonymous request, it is the fully
    authenticated user reaching for somebody else's row.
    """

    def test_cannot_read_another_users_item(self, client, other_users_item):
        response = client.get(f"/api/filesystem/{other_users_item.id}")
        assert response.status_code == 404

    def test_cannot_list_another_users_folder_contents(self, client, other_users_item):
        response = client.get(f"/api/filesystem?parent_id={other_users_item.id}")
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            assert json.loads(response.data)["items"] == []

    def test_cannot_update_another_users_item(self, client, other_users_item):
        response = client.put(
            f"/api/filesystem/{other_users_item.id}",
            json={"name": "renamed by an outsider"},
        )
        assert response.status_code == 404

    def test_cannot_delete_another_users_item(self, client, other_users_item):
        response = client.delete(f"/api/filesystem/{other_users_item.id}")
        assert response.status_code == 404

    def test_owner_still_sees_their_own_item(self, other_client, other_users_item):
        """The mirror of the tests above: the real owner is not locked out."""
        response = other_client.get(f"/api/filesystem/{other_users_item.id}")
        assert response.status_code == 200
        assert json.loads(response.data)["name"] == "Private"

    def test_listing_is_scoped_to_the_caller(self, client, other_client, sample_item):  # noqa: ARG002
        """Two users, one database, disjoint views."""
        mine = json.loads(client.get("/api/filesystem").data)["items"]
        theirs = json.loads(other_client.get("/api/filesystem").data)["items"]

        assert any(item["name"] == "Test Folder" for item in mine)
        assert all(item["name"] != "Test Folder" for item in theirs)


class TestPagination:
    def test_listing_is_paginated(self, client):
        response = client.get("/api/filesystem")
        body = json.loads(response.data)
        assert {"items", "total", "limit", "offset", "has_more"} <= set(body)

    def test_limit_is_respected(self, client, app):
        from database import db
        from models import FileSystemItem, User

        with app.app_context():
            user = User.query.filter_by(auth0_id="auth0|owner").first()
            for index in range(12):
                db.session.add(FileSystemItem(name=f"folder-{index}", type="folder", owner_id=user.id, parent_id=None))
            db.session.commit()

        body = json.loads(client.get("/api/filesystem?limit=5").data)
        assert len(body["items"]) == 5
        assert body["total"] == 12
        assert body["has_more"] is True

    def test_limit_is_capped(self, client):
        """A caller must not be able to ask for everything."""
        body = json.loads(client.get("/api/filesystem?limit=100000").data)
        assert body["limit"] <= 500

    def test_garbage_limit_falls_back_to_the_default(self, client):
        body = json.loads(client.get("/api/filesystem?limit=abc&offset=xyz").data)
        assert body["limit"] == 100
        assert body["offset"] == 0
