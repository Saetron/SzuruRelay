import asyncio
import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import httpx
from config import config
from services.auth import get_auth_headers
from models.converters import is_post_favorited_by
from services.http_client import get_http_client
from utils import strip_json_suffix

logger = logging.getLogger(__name__)
favorites_router = APIRouter()

_ID_SPLIT_TABLE = str.maketrans({",": " ", "+": " "})


def _build_favorite_entry(pid: int, created_at: str) -> Dict[str, Any]:
    return {
        "id": pid,
        "user_id": 1,
        "post_id": pid,
        "created_at": created_at,
        "updated_at": created_at,
        "score": 1,
        "is_deleted": False,
    }


async def _extract_post_id(request: Request) -> Optional[int]:
    """Safely extract post_id from query params, form values, or JSON body"""
    post_id = request.query_params.get("post_id")
    if not post_id:
        content_type = request.headers.get("content-type", "").lower()
        if "application/json" in content_type:
            try:
                json_data = await request.json()
                if isinstance(json_data, dict):
                    post_id = json_data.get("post_id")
            except Exception:
                pass
        elif "form" in content_type:
            try:
                form_data = await request.form()
                post_id = form_data.get("post_id")
            except Exception:
                pass

    if not post_id:
        try:
            raw_body = (await request.body()).decode("utf-8", errors="ignore")
            if "post_id=" in raw_body:
                for part in raw_body.split("&"):
                    if part.startswith("post_id="):
                        post_id = part.partition("=")[2]
                        break
        except Exception:
            pass

    if post_id is not None:
        try:
            return int(post_id)
        except (ValueError, TypeError):
            return None
    return None


@favorites_router.post("/favorites.json")
@favorites_router.post("/favorites")
@favorites_router.post("/post_votes.json")
@favorites_router.post("/post_votes")
async def create_favorite(request: Request):
    post_id = await _extract_post_id(request)
    if not post_id:
        return JSONResponse({"message": "post_id is required"}, status_code=400)

    headers, _, _ = await get_auth_headers(request)
    client = get_http_client()

    try:
        response = await client.post(
            f"{config.SZURUBOORU_API_URL}/post/{post_id}/favorite",
            headers=headers,
            timeout=15.0,
        )
        if response.status_code in (200, 201):
            return JSONResponse(
                {
                    "id": post_id,
                    "user_id": 1,
                    "post_id": post_id,
                    "message": "Favorite created",
                },
                status_code=200,
            )
        else:
            return JSONResponse(
                {"message": "Failed to create favorite"},
                status_code=response.status_code,
            )
    except httpx.RequestError as e:
        logger.error(f"Error creating favorite for post {post_id}: {e}")
        return JSONResponse({"message": "API request failed"}, status_code=500)


@favorites_router.delete("/favorites/{post_id}.json")
@favorites_router.delete("/favorites/{post_id}")
async def delete_favorite(post_id: str, request: Request):
    clean_id = strip_json_suffix(post_id)
    try:
        pid = int(clean_id)
    except ValueError:
        return JSONResponse({"message": "Invalid post ID"}, status_code=400)

    headers, _, _ = await get_auth_headers(request)
    client = get_http_client()

    try:
        response = await client.delete(
            f"{config.SZURUBOORU_API_URL}/post/{pid}/favorite",
            headers=headers,
            timeout=15.0,
        )
        if response.status_code in (200, 204):
            return JSONResponse({"message": "Favorite deleted"}, status_code=200)
        else:
            return JSONResponse(
                {"message": "Failed to delete favorite"},
                status_code=response.status_code,
            )
    except httpx.RequestError as e:
        logger.error(f"Error deleting favorite for post {pid}: {e}")
        return JSONResponse({"message": "API request failed"}, status_code=500)


async def _check_post_favorite(
    client: httpx.AsyncClient,
    pid: int,
    headers: dict,
    login: Optional[str],
) -> Optional[Dict[str, Any]]:
    try:
        res = await client.get(
            f"{config.SZURUBOORU_API_URL}/post/{pid}",
            headers=headers,
            timeout=5.0,
        )
        if res.status_code == 200:
            szuru_post = res.json()
            if is_post_favorited_by(szuru_post, login):
                return _build_favorite_entry(pid, szuru_post.get("creationTime", ""))
    except httpx.RequestError:
        pass
    return None


@favorites_router.get("/post_votes.json")
@favorites_router.get("/post_votes")
@favorites_router.get("/favorites.json")
@favorites_router.get("/favorites")
async def get_favorites(request: Request):
    headers, login, _ = await get_auth_headers(request)

    raw_post_ids = (
        request.query_params.get("search[post_id]")
        or request.query_params.get("post_id")
        or ""
    )

    clean_ids = [
        int(item)
        for item in raw_post_ids.translate(_ID_SPLIT_TABLE).split()
        if item.isdigit()
    ] if raw_post_ids else []

    favorites = []
    client = get_http_client()

    # If specific post IDs were requested, check them concurrently
    if clean_ids:
        results = await asyncio.gather(
            *(_check_post_favorite(client, pid, headers, login) for pid in clean_ids)
        )
        favorites = [entry for entry in results if entry is not None]
    elif login:
        # If no specific post_ids requested, fetch user's favorites from Szurubooru
        try:
            res = await client.get(
                f"{config.SZURUBOORU_API_URL}/posts",
                params={"query": f"fav:{login}", "limit": 100},
                headers=headers,
                timeout=15.0,
            )
            if res.status_code == 200:
                data = res.json()
                for post in data.get("results", []):
                    pid = post.get("id")
                    if pid:
                        favorites.append(
                            _build_favorite_entry(pid, post.get("creationTime", ""))
                        )
        except httpx.RequestError as e:
            logger.warning(f"Failed to fetch favorites for user {login}: {e}")

    return JSONResponse(favorites, status_code=200)

