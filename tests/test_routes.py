import base64
from unittest.mock import patch, AsyncMock, MagicMock
import httpx
import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request
from app import create_app
from services.auth import extract_auth_from_request


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_proxy_path_traversal_blocked(client):
    response = client.get("/data/../../etc/passwd")
    assert response.status_code in (403, 404)


@patch("routes.posts.get_http_client")
def test_counts_posts(mock_get_client, client):
    mock_client = AsyncMock()
    mock_client.get.return_value = httpx.Response(200, json={"total": 5432})
    mock_get_client.return_value = mock_client

    response = client.get("/counts/posts.json?tags=cat")
    assert response.status_code == 200
    data = response.json()
    assert "counts" in data
    assert "posts" in data["counts"]
    assert data["counts"]["posts"] == 5432


@patch("routes.posts.get_http_client")
def test_search_posts(mock_get_client, client):
    mock_client = AsyncMock()
    mock_client.get.return_value = httpx.Response(
        200,
        json={
            "results": [
                {
                    "id": 1,
                    "creationTime": "2023-01-01T00:00:00Z",
                    "contentUrl": "data/1.png",
                    "thumbnailUrl": "thumbnails/1.jpg",
                    "tags": [{"names": ["cat"], "category": "general"}],
                    "safety": "safe",
                    "score": 5,
                }
            ],
            "total": 1,
        },
    )
    mock_get_client.return_value = mock_client

    response = client.get("/posts.json?tags=cat&limit=20&page=1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["rating"] == "s"
    assert data[0]["tag_string"] == "cat"


@patch("routes.posts.get_http_client")
def test_get_single_post(mock_get_client, client):
    mock_client = AsyncMock()
    mock_client.get.return_value = httpx.Response(
        200,
        json={
            "id": 100,
            "creationTime": "2023-01-01T00:00:00Z",
            "contentUrl": "data/100.png",
            "thumbnailUrl": "thumbnails/100.jpg",
            "tags": [],
            "safety": "sketchy",
            "score": 2,
        },
    )
    mock_get_client.return_value = mock_client

    response = client.get("/posts/100.json")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 100
    assert data["rating"] == "q"


def test_favorites_empty_post_id_no_crash(client):
    response = client.get("/favorites.json")
    assert response.status_code == 200
    assert response.json() == []


@patch("routes.favorites.get_http_client")
def test_create_favorite(mock_get_client, client):
    mock_client = AsyncMock()
    mock_client.post.return_value = httpx.Response(200, json={})
    mock_get_client.return_value = mock_client

    response = client.post("/favorites.json", json={"post_id": 42})
    assert response.status_code == 200
    data = response.json()
    assert data["post_id"] == 42
    assert data["message"] == "Favorite created"


@patch("routes.favorites.get_http_client")
def test_delete_favorite(mock_get_client, client):
    mock_client = AsyncMock()
    mock_client.delete.return_value = httpx.Response(200, json={})
    mock_get_client.return_value = mock_client

    response = client.delete("/favorites/42.json")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Favorite deleted"


@patch("routes.tags.get_http_client")
def test_tags_autocomplete(mock_get_client, client):
    mock_client = AsyncMock()
    mock_client.get.return_value = httpx.Response(
        200,
        json={
            "results": [
                {"names": ["cat"], "category": "general", "usages": 10},
                {"names": ["catherine"], "category": "character", "usages": 2},
            ]
        },
    )
    mock_get_client.return_value = mock_client

    response = client.get("/autocomplete.json?q=cat")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["label"] == "cat"
    assert data[0]["category"] == 0
    assert data[1]["label"] == "catherine"
    assert data[1]["category"] == 4


@patch("routes.tags.get_http_client")
def test_search_tags(mock_get_client, client):
    mock_client = AsyncMock()
    mock_client.get.return_value = httpx.Response(
        200,
        json={
            "results": [
                {"names": ["artist_name"], "category": "artist", "usages": 50}
            ]
        },
    )
    mock_get_client.return_value = mock_client

    response = client.get("/tags.json?name=artist_name")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "artist_name"
    assert data[0]["category"] == 1


@pytest.mark.asyncio
async def test_auth_extraction_with_colon_in_password():
    credentials = "myuser:pass:word:123"
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("ascii")

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/posts.json",
        "headers": [(b"authorization", f"Basic {encoded}".encode("ascii"))],
        "query_string": b"",
    }
    req = Request(scope)
    login, api_key = await extract_auth_from_request(req)
    assert login == "myuser"
    assert api_key == "pass:word:123"


@patch("routes.users.get_http_client")
def test_profile_authenticated(mock_get_client, client):
    mock_client = AsyncMock()
    mock_client.get.return_value = httpx.Response(
        200,
        json={
            "name": "testuser",
            "rank": "administrator",
            "creationTime": "2023-01-01T00:00:00Z",
            "lastLoginTime": "2023-01-02T00:00:00Z",
            "uploadedPostCount": 10,
            "favoritePostCount": 5,
            "commentCount": 2,
        },
    )
    mock_get_client.return_value = mock_client

    response = client.get("/profile.json?login=testuser&api_key=secretpass")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "testuser"
    assert data["level"] == 50
    assert data["level_string"] == "Admin"
    assert data["post_upload_count"] == 10
    assert data["favorite_count"] == 5


def test_admin_timing_endpoints(client):
    r1 = client.post("/admin/timing/enable")
    assert r1.status_code == 200
    assert r1.json()["status"] == "enabled"

    r2 = client.get("/admin/timing/status")
    assert r2.status_code == 200
    assert r2.json()["status"] == "enabled"

    r3 = client.post("/admin/timing/toggle")
    assert r3.status_code == 200
    assert r3.json()["status"] == "disabled"

    r4 = client.post("/admin/timing/disable")
    assert r4.status_code == 200
    assert r4.json()["status"] == "disabled"
