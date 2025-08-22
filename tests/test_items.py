import pytest
from httpx import AsyncClient


class TestItems:
    """Test item endpoints."""

    @pytest.mark.firebase
    async def test_create_item(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_item_data: dict,
        clean_firestore,
    ):
        """Test creating an item."""
        response = await client.post(
            "/api/v1/items", json=test_item_data, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == test_item_data["title"]
        assert data["description"] == test_item_data["description"]
        assert data["category"] == test_item_data["category"]
        assert data["priority"] == test_item_data["priority"]
        assert data["status"] == test_item_data["status"]
        assert data["tags"] == test_item_data["tags"]
        assert data["is_public"] == test_item_data["is_public"]
        assert "owner_uid" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_item_unauthenticated(
        self, client: AsyncClient, test_item_data: dict
    ):
        """Test creating item without authentication fails."""
        response = await client.post("/api/v1/items", json=test_item_data)
        assert response.status_code == 403

    @pytest.mark.firebase
    async def test_create_item_invalid_data(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating item with invalid data."""
        invalid_data = {
            "title": "",  # Empty title
            "category": "invalid_category",
            "priority": "invalid_priority",
        }

        response = await client.post(
            "/api/v1/items", json=invalid_data, headers=auth_headers
        )
        assert response.status_code == 422

    @pytest.mark.firebase
    async def test_get_item_public(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_item_data: dict,
        clean_firestore,
    ):
        """Test getting a public item."""
        # Create public item
        create_response = await client.post(
            "/api/v1/items",
            json={**test_item_data, "is_public": True},
            headers=auth_headers,
        )
        assert create_response.status_code == 200
        item_id = create_response.json()["id"]

        # Get item without authentication (should work for public items)
        response = await client.get(f"/api/v1/items/{item_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item_id
        assert data["is_public"] == True

    @pytest.mark.firebase
    async def test_get_item_private_owner(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_item_data: dict,
        clean_firestore,
    ):
        """Test getting a private item as owner."""
        # Create private item
        create_response = await client.post(
            "/api/v1/items",
            json={**test_item_data, "is_public": False},
            headers=auth_headers,
        )
        assert create_response.status_code == 200
        item_id = create_response.json()["id"]

        # Get item as owner
        response = await client.get(f"/api/v1/items/{item_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item_id
        assert data["is_public"] == False

    @pytest.mark.firebase
    async def test_get_item_private_unauthorized(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_item_data: dict,
        clean_firestore,
    ):
        """Test getting a private item without authorization fails."""
        # Create private item
        create_response = await client.post(
            "/api/v1/items",
            json={**test_item_data, "is_public": False},
            headers=auth_headers,
        )
        assert create_response.status_code == 200
        item_id = create_response.json()["id"]

        # Try to get item without authentication
        response = await client.get(f"/api/v1/items/{item_id}")
        assert response.status_code == 403

    @pytest.mark.firebase
    async def test_get_nonexistent_item(self, client: AsyncClient):
        """Test getting non-existent item returns 404."""
        response = await client.get("/api/v1/items/nonexistent-id")
        assert response.status_code == 404

    @pytest.mark.firebase
    async def test_update_item_owner(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_item_data: dict,
        clean_firestore,
    ):
        """Test updating item as owner."""
        # Create item
        create_response = await client.post(
            "/api/v1/items", json=test_item_data, headers=auth_headers
        )
        assert create_response.status_code == 200
        item_id = create_response.json()["id"]

        # Update item
        update_data = {
            "title": "Updated Test Item",
            "status": "active",
            "priority": "high",
        }

        response = await client.put(
            f"/api/v1/items/{item_id}", json=update_data, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["status"] == update_data["status"]
        assert data["priority"] == update_data["priority"]

    @pytest.mark.firebase
    async def test_update_item_unauthorized(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_item_data: dict,
        clean_firestore,
    ):
        """Test updating item without authorization fails."""
        # Create item
        create_response = await client.post(
            "/api/v1/items", json=test_item_data, headers=auth_headers
        )
        assert create_response.status_code == 200
        item_id = create_response.json()["id"]

        # Try to update without authentication
        response = await client.put(
            f"/api/v1/items/{item_id}", json={"title": "Hacked Title"}
        )
        assert response.status_code == 403

    @pytest.mark.firebase
    async def test_delete_item_owner(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_item_data: dict,
        clean_firestore,
    ):
        """Test deleting item as owner."""
        # Create item
        create_response = await client.post(
            "/api/v1/items", json=test_item_data, headers=auth_headers
        )
        assert create_response.status_code == 200
        item_id = create_response.json()["id"]

        # Delete item
        response = await client.delete(f"/api/v1/items/{item_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "deleted" in data["message"].lower()

        # Verify item is deleted
        get_response = await client.get(f"/api/v1/items/{item_id}")
        assert get_response.status_code == 404

    @pytest.mark.firebase
    async def test_delete_item_unauthorized(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_item_data: dict,
        clean_firestore,
    ):
        """Test deleting item without authorization fails."""
        # Create item
        create_response = await client.post(
            "/api/v1/items", json=test_item_data, headers=auth_headers
        )
        assert create_response.status_code == 200
        item_id = create_response.json()["id"]

        # Try to delete without authentication
        response = await client.delete(f"/api/v1/items/{item_id}")
        assert response.status_code == 403

    @pytest.mark.firebase
    async def test_list_items_public(
        self, client: AsyncClient, auth_headers: dict, clean_firestore
    ):
        """Test listing public items."""
        # Create some public and private items
        public_item_data = {
            "title": "Public Item",
            "is_public": True,
            "category": "general",
            "priority": "medium",
            "status": "draft",
        }
        private_item_data = {
            "title": "Private Item",
            "is_public": False,
            "category": "general",
            "priority": "medium",
            "status": "draft",
        }

        await client.post("/api/v1/items", json=public_item_data, headers=auth_headers)
        await client.post("/api/v1/items", json=private_item_data, headers=auth_headers)

        # List items without authentication (should only see public items)
        response = await client.get("/api/v1/items")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data

        # Should only see public items
        public_items = [
            item for item in data["items"] if item["title"] == "Public Item"
        ]
        private_items = [
            item for item in data["items"] if item["title"] == "Private Item"
        ]
        assert len(public_items) >= 1
        assert len(private_items) == 0

    @pytest.mark.firebase
    async def test_list_items_with_filters(
        self, client: AsyncClient, auth_headers: dict, clean_firestore
    ):
        """Test listing items with filters."""
        # Create items with different categories
        tech_item = {
            "title": "Tech Item",
            "category": "tech",
            "is_public": True,
            "priority": "medium",
            "status": "draft",
        }
        business_item = {
            "title": "Business Item",
            "category": "business",
            "is_public": True,
            "priority": "high",
            "status": "active",
        }

        await client.post("/api/v1/items", json=tech_item, headers=auth_headers)
        await client.post("/api/v1/items", json=business_item, headers=auth_headers)

        # Filter by category
        response = await client.get("/api/v1/items?category=tech")
        assert response.status_code == 200
        data = response.json()
        tech_items = [item for item in data["items"] if item["category"] == "tech"]
        business_items = [
            item for item in data["items"] if item["category"] == "business"
        ]
        assert len(tech_items) >= 1
        assert len(business_items) == 0

        # Filter by priority
        response = await client.get("/api/v1/items?priority=high")
        assert response.status_code == 200
        data = response.json()
        high_priority_items = [
            item for item in data["items"] if item["priority"] == "high"
        ]
        assert len(high_priority_items) >= 1

    @pytest.mark.firebase
    async def test_item_interaction_like(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_item_data: dict,
        clean_firestore,
    ):
        """Test liking an item."""
        # Create public item
        create_response = await client.post(
            "/api/v1/items",
            json={**test_item_data, "is_public": True},
            headers=auth_headers,
        )
        assert create_response.status_code == 200
        item_id = create_response.json()["id"]

        # Like the item
        response = await client.post(
            f"/api/v1/items/{item_id}/interact",
            json={"interaction_type": "like"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["interaction_type"] == "like"
        assert data["success"] == True
        assert data["new_count"] > 0

    @pytest.mark.firebase
    async def test_item_interaction_share(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_item_data: dict,
        clean_firestore,
    ):
        """Test sharing an item."""
        # Create public item
        create_response = await client.post(
            "/api/v1/items",
            json={**test_item_data, "is_public": True},
            headers=auth_headers,
        )
        assert create_response.status_code == 200
        item_id = create_response.json()["id"]

        # Share the item
        response = await client.post(
            f"/api/v1/items/{item_id}/interact",
            json={"interaction_type": "share", "metadata": {"platform": "twitter"}},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["interaction_type"] == "share"
        assert data["success"] == True
        assert data["new_count"] > 0

    @pytest.mark.firebase
    async def test_item_interaction_invalid_type(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_item_data: dict,
        clean_firestore,
    ):
        """Test invalid interaction type."""
        # Create public item
        create_response = await client.post(
            "/api/v1/items",
            json={**test_item_data, "is_public": True},
            headers=auth_headers,
        )
        assert create_response.status_code == 200
        item_id = create_response.json()["id"]

        # Try invalid interaction
        response = await client.post(
            f"/api/v1/items/{item_id}/interact",
            json={"interaction_type": "invalid"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    @pytest.mark.firebase
    @pytest.mark.admin
    async def test_get_item_stats_admin(self, client: AsyncClient, admin_user: dict):
        """Test getting item statistics as admin."""
        response = await client.get(
            "/api/v1/items/stats/overview", headers=admin_user["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_items" in data
        assert "items_by_status" in data
        assert "items_by_category" in data
        assert "items_by_priority" in data
        assert "public_items" in data
        assert "private_items" in data
        assert isinstance(data["total_items"], int)
        assert isinstance(data["items_by_status"], dict)
        assert isinstance(data["items_by_category"], dict)
        assert isinstance(data["items_by_priority"], dict)

    @pytest.mark.firebase
    async def test_get_item_stats_regular_user_forbidden(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting item statistics as regular user is forbidden."""
        response = await client.get(
            "/api/v1/items/stats/overview", headers=auth_headers
        )
        assert response.status_code == 403
