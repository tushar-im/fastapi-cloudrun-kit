import pytest
from httpx import AsyncClient


class TestUsers:
    """Test user endpoints."""

    @pytest.mark.firebase
    async def test_get_my_profile(self, client: AsyncClient, auth_headers: dict):
        """Test getting current user's profile."""
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "uid" in data
        assert "email" in data
        assert "display_name" in data
        assert "profile" in data
        assert "preferences" in data

    @pytest.mark.firebase
    async def test_update_my_profile(self, client: AsyncClient, auth_headers: dict):
        """Test updating current user's profile."""
        update_data = {
            "display_name": "Updated Test User",
            "profile": {"bio": "This is my updated bio", "location": "Test City"},
        }

        response = await client.put(
            "/api/v1/users/me", json=update_data, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == update_data["display_name"]
        assert data["profile"]["bio"] == update_data["profile"]["bio"]
        assert data["profile"]["location"] == update_data["profile"]["location"]

    @pytest.mark.firebase
    async def test_update_my_profile_details(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test updating profile details."""
        profile_update = {
            "bio": "New bio",
            "website": "https://example.com",
            "company": "Test Company",
        }

        response = await client.put(
            "/api/v1/users/me/profile", json=profile_update, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["profile"]["bio"] == profile_update["bio"]
        assert data["profile"]["website"] == profile_update["website"]
        assert data["profile"]["company"] == profile_update["company"]

    @pytest.mark.firebase
    async def test_update_my_preferences(self, client: AsyncClient, auth_headers: dict):
        """Test updating user preferences."""
        preferences_update = {
            "notifications_email": False,
            "theme": "dark",
            "language": "es",
        }

        response = await client.put(
            "/api/v1/users/me/preferences",
            json=preferences_update,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["preferences"]["notifications_email"] == False
        assert data["preferences"]["theme"] == "dark"
        assert data["preferences"]["language"] == "es"

    @pytest.mark.firebase
    async def test_get_user_by_id_own_user(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting user by ID (own user)."""
        # First get current user to get UID
        me_response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert me_response.status_code == 200
        uid = me_response.json()["uid"]

        # Now get user by ID
        response = await client.get(f"/api/v1/users/{uid}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["uid"] == uid

    @pytest.mark.firebase
    async def test_get_user_by_id_other_user_forbidden(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting other user by ID is forbidden for regular users."""
        response = await client.get("/api/v1/users/other-user-id", headers=auth_headers)
        assert response.status_code == 403

    @pytest.mark.firebase
    @pytest.mark.admin
    async def test_list_users_admin(self, client: AsyncClient, admin_user: dict):
        """Test listing users as admin."""
        response = await client.get("/api/v1/users", headers=admin_user["headers"])
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert isinstance(data["users"], list)

    @pytest.mark.firebase
    async def test_list_users_regular_user_forbidden(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing users as regular user is forbidden."""
        response = await client.get("/api/v1/users", headers=auth_headers)
        assert response.status_code == 403

    @pytest.mark.firebase
    @pytest.mark.admin
    async def test_create_user_admin(
        self, client: AsyncClient, admin_user: dict, clean_firestore
    ):
        """Test creating user as admin."""
        new_user_data = {
            "email": "newuser@example.com",
            "password": "NewUserPassword123!",
            "display_name": "New User",
            "email_verified": True,
            "disabled": False,
        }

        response = await client.post(
            "/api/v1/users", json=new_user_data, headers=admin_user["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == new_user_data["email"]
        assert data["display_name"] == new_user_data["display_name"]
        assert data["email_verified"] == new_user_data["email_verified"]
        assert data["disabled"] == new_user_data["disabled"]

    @pytest.mark.firebase
    async def test_create_user_regular_user_forbidden(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating user as regular user is forbidden."""
        new_user_data = {
            "email": "newuser@example.com",
            "password": "NewUserPassword123!",
            "display_name": "New User",
        }

        response = await client.post(
            "/api/v1/users", json=new_user_data, headers=auth_headers
        )
        assert response.status_code == 403

    @pytest.mark.firebase
    @pytest.mark.admin
    async def test_update_user_admin(self, client: AsyncClient, admin_user: dict):
        """Test updating user as admin."""
        # First create a user to update
        create_response = await client.post(
            "/api/v1/users",
            json={
                "email": "updateuser@example.com",
                "password": "UpdateUserPassword123!",
                "display_name": "Update User",
            },
            headers=admin_user["headers"],
        )
        assert create_response.status_code == 200
        created_user = create_response.json()

        # Now update the user
        update_data = {
            "display_name": "Updated User Name",
            "disabled": True,
            "email_verified": True,
        }

        response = await client.put(
            f"/api/v1/users/{created_user['uid']}",
            json=update_data,
            headers=admin_user["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == update_data["display_name"]
        assert data["disabled"] == update_data["disabled"]
        assert data["email_verified"] == update_data["email_verified"]

    @pytest.mark.firebase
    @pytest.mark.admin
    async def test_delete_user_admin(self, client: AsyncClient, admin_user: dict):
        """Test deleting user as admin."""
        # First create a user to delete
        create_response = await client.post(
            "/api/v1/users",
            json={
                "email": "deleteuser@example.com",
                "password": "DeleteUserPassword123!",
                "display_name": "Delete User",
            },
            headers=admin_user["headers"],
        )
        assert create_response.status_code == 200
        created_user = create_response.json()

        # Now delete the user
        response = await client.delete(
            f"/api/v1/users/{created_user['uid']}", headers=admin_user["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "deleted" in data["message"].lower()

    @pytest.mark.firebase
    async def test_delete_my_account(self, client: AsyncClient, auth_headers: dict):
        """Test deleting own account."""
        response = await client.delete("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "deleted" in data["message"].lower()

    @pytest.mark.firebase
    @pytest.mark.admin
    async def test_assign_roles_admin(self, client: AsyncClient, admin_user: dict):
        """Test assigning roles as admin."""
        # First create a user
        create_response = await client.post(
            "/api/v1/users",
            json={
                "email": "roleuser@example.com",
                "password": "RoleUserPassword123!",
                "display_name": "Role User",
            },
            headers=admin_user["headers"],
        )
        assert create_response.status_code == 200
        created_user = create_response.json()

        # Assign roles
        response = await client.post(
            "/api/v1/users/roles/assign",
            json={
                "user_uid": created_user["uid"],
                "roles": ["moderator", "beta_tester"],
            },
            headers=admin_user["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "assigned" in data["message"].lower()

    @pytest.mark.firebase
    async def test_assign_roles_regular_user_forbidden(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test assigning roles as regular user is forbidden."""
        response = await client.post(
            "/api/v1/users/roles/assign",
            json={"user_uid": "some-user-id", "roles": ["moderator"]},
            headers=auth_headers,
        )
        assert response.status_code == 403

    @pytest.mark.firebase
    @pytest.mark.admin
    async def test_get_user_stats_admin(self, client: AsyncClient, admin_user: dict):
        """Test getting user statistics as admin."""
        response = await client.get(
            "/api/v1/users/stats/overview", headers=admin_user["headers"]
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "active_users" in data
        assert "verified_users" in data
        assert "disabled_users" in data
        assert isinstance(data["total_users"], int)

    @pytest.mark.firebase
    async def test_get_user_stats_regular_user_forbidden(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting user statistics as regular user is forbidden."""
        response = await client.get(
            "/api/v1/users/stats/overview", headers=auth_headers
        )
        assert response.status_code == 403
