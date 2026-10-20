import logging
from typing import Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import httpx
from config import config
from services.auth import get_auth_headers
from models.converters import is_post_favorited_by
from services.http_client import get_http_client

logger = logging.getLogger(__name__)
favorites_router = APIRouter()


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
                        post_id = part.split("=", 1)[1]
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
    clean_id = post_id[:-5] if post_id.endswith(".json") else post_id
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

    clean_ids = []
    if raw_post_ids:
        # Split by comma, plus, or space
        normalized = raw_post_ids.replace(",", " ").replace("+", " ")
        for item in normalized.split():
            item_str = item.strip()
            if item_str.isdigit():
                clean_ids.append(int(item_str))

    favorites = []
    client = get_http_client()

    # If specific post IDs were requested, check them
    if clean_ids:
        for pid in clean_ids:
            try:
                res = await client.get(
                    f"{config.SZURUBOORU_API_URL}/post/{pid}",
                    headers=headers,
                    timeout=5.0,
                )
                if res.status_code == 200:
                    szuru_post = res.json()
                    if is_post_favorited_by(szuru_post, login):
                        favorites.append(
                            {
                                "id": pid,
                                "user_id": 1,
                                "post_id": pid,
                                "created_at": szuru_post.get("creationTime", ""),
                                "updated_at": szuru_post.get("creationTime", ""),
                                "score": 1,
                                "is_deleted": False,
                            }
                        )
            except httpx.RequestError:
                continue
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
                            {
                                "id": pid,
                                "user_id": 1,
                                "post_id": pid,
                                "created_at": post.get("creationTime", ""),
                                "updated_at": post.get("creationTime", ""),
                                "score": 1,
                                "is_deleted": False,
                            }
                        )
        except httpx.RequestError as e:
            logger.warning(f"Failed to fetch favorites for user {login}: {e}")

    return JSONResponse(favorites, status_code=200)
