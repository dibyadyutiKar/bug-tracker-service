"""Project endpoint integration tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.project import Project


@pytest.mark.asyncio
async def test_list_projects_empty(client: AsyncClient, auth_headers: dict):
    """Test listing projects when none exist."""
    response = await client.get(
        "/api/v1/projects",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_project_as_manager(
    client: AsyncClient,
    manager_auth_headers: dict,
):
    """Test creating a project as manager."""
    response = await client.post(
        "/api/v1/projects",
        headers=manager_auth_headers,
        json={
            "name": "Test Project",
            "description": "A test project description",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["description"] == "A test project description"
    assert data["is_archived"] is False


@pytest.mark.asyncio
async def test_create_project_as_developer(
    client: AsyncClient,
    auth_headers: dict,
):
    """Test that developers cannot create projects."""
    response = await client.post(
        "/api/v1/projects",
        headers=auth_headers,
        json={
            "name": "Test Project",
            "description": "A test project description",
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_project_duplicate_name(
    client: AsyncClient,
    manager_auth_headers: dict,
):
    """Test creating a project with duplicate name."""
    # Create first project
    await client.post(
        "/api/v1/projects",
        headers=manager_auth_headers,
        json={"name": "Duplicate Name"},
    )

    # Try to create second project with same name
    response = await client.post(
        "/api/v1/projects",
        headers=manager_auth_headers,
        json={"name": "Duplicate Name"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_project(
    client: AsyncClient,
    manager_auth_headers: dict,
    auth_headers: dict,
):
    """Test getting a single project."""
    # Create project
    create_response = await client.post(
        "/api/v1/projects",
        headers=manager_auth_headers,
        json={"name": "Get Test Project"},
    )
    project_id = create_response.json()["id"]

    # Get project as developer
    response = await client.get(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Get Test Project"
    assert "issue_count" in data
    assert "open_issue_count" in data


@pytest.mark.asyncio
async def test_update_project_as_owner(
    client: AsyncClient,
    manager_auth_headers: dict,
):
    """Test updating a project as owner."""
    # Create project
    create_response = await client.post(
        "/api/v1/projects",
        headers=manager_auth_headers,
        json={"name": "Update Test Project"},
    )
    project_id = create_response.json()["id"]

    # Update project
    response = await client.patch(
        f"/api/v1/projects/{project_id}",
        headers=manager_auth_headers,
        json={"name": "Updated Project Name"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Project Name"


@pytest.mark.asyncio
async def test_update_project_as_non_owner(
    client: AsyncClient,
    manager_auth_headers: dict,
    auth_headers: dict,
):
    """Test that non-owners cannot update projects."""
    # Create project as manager
    create_response = await client.post(
        "/api/v1/projects",
        headers=manager_auth_headers,
        json={"name": "Non-Owner Update Test"},
    )
    project_id = create_response.json()["id"]

    # Try to update as developer
    response = await client.patch(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers,
        json={"name": "Should Fail"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_archive_project(
    client: AsyncClient,
    manager_auth_headers: dict,
):
    """Test archiving a project."""
    # Create project
    create_response = await client.post(
        "/api/v1/projects",
        headers=manager_auth_headers,
        json={"name": "Archive Test Project"},
    )
    project_id = create_response.json()["id"]

    # Archive project
    response = await client.delete(
        f"/api/v1/projects/{project_id}",
        headers=manager_auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["is_archived"] is True


@pytest.mark.asyncio
async def test_list_projects_with_pagination(
    client: AsyncClient,
    manager_auth_headers: dict,
    auth_headers: dict,
):
    """Test listing projects with pagination."""
    # Create multiple projects
    for i in range(5):
        await client.post(
            "/api/v1/projects",
            headers=manager_auth_headers,
            json={"name": f"Project {i}"},
        )

    # Get first page
    response = await client.get(
        "/api/v1/projects",
        headers=auth_headers,
        params={"page": 1, "limit": 2},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["total_pages"] == 3
