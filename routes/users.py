import logging
from typing import Any, Dict, Optional, Tuple
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import httpx
from config import config
from services.auth import get_auth_headers
from models.converters import convert_user_format
from services.http_client import get_http_client
from utils import strip_json_suffix

logger = logging.getLogger(__name__)
users_router = APIRouter()


async def _fetch_szuru_user(
    client: httpx.AsyncClient,
    target_user: str,
    headers: dict,
) -> Tuple[Optional[Dict[str, Any]], int]:
    """Fetch a user from Szurubooru by direct endpoint with fallback to user search"""
    response = await client.get(
        f"{config.SZURUBOORU_API_URL}/user/{target_user}",
        headers=headers,
        timeout=10.0,
    )
    if response.status_code == 200:
        return response.json(), 200

    fallback_resp = await client.get(
        f"{config.SZURUBOORU_API_URL}/users",
        params={"query": target_user},
        headers=headers,
        timeout=10.0,
    )
    if fallback_resp.status_code == 200:
        results = fallback_resp.json().get("results", [])
        if results:
            return results[0], 200

    return None, response.status_code


@users_router.get("/users/{user_identifier}.json")
@users_router.get("/users/{user_identifier}")
async def get_user(user_identifier: str, request: Request):
    headers, login, _ = await get_auth_headers(request)
    clean_id = strip_json_suffix(user_identifier)
    target_user = login if (clean_id.isdigit() and login) else clean_id

    client = get_http_client()
    try:
        user_obj, status_code = await _fetch_szuru_user(client, target_user, headers)
        if user_obj is not None:
            profile = convert_user_format(user_obj)
            if clean_id.isdigit():
                profile["id"] = int(clean_id)
            return JSONResponse(profile, status_code=200)

        if status_code in (401, 403):
            return JSONResponse({"message": "Access denied"}, status_code=status_code)

        return JSONResponse({"message": "Profile not found"}, status_code=404)
    except httpx.RequestError as e:
        logger.error(f"Error fetching user {clean_id}: {e}")
        return JSONResponse(convert_user_format({}), status_code=200)


@users_router.get("/users.json")
@users_router.get("/users")
async def search_users(request: Request):
    headers, login, _ = await get_auth_headers(request)
    name_query = (
        request.query_params.get("search[name_matches]")
        or request.query_params.get("search[name]")
        or request.query_params.get("name")
        or login
        or ""
    ).strip()

    client = get_http_client()
    try:
        response = await client.get(
            f"{config.SZURUBOORU_API_URL}/users",
            params={"query": name_query} if name_query else {},
            headers=headers,
            timeout=10.0,
        )
        if response.status_code == 200:
            data = response.json()
            users_list = [
                convert_user_format(item) for item in data.get("results", [])
            ]
            return JSONResponse(users_list, status_code=200)
        else:
            return JSONResponse([], status_code=response.status_code)
    except httpx.RequestError as e:
        logger.error(f"Error searching users: {e}")
        return JSONResponse([], status_code=200)


@users_router.get("/profile")
@users_router.get("/profile.json")
async def get_profile(request: Request):
    headers, login, _ = await get_auth_headers(request)
    if not login:
        return JSONResponse(convert_user_format({}), status_code=200)

    client = get_http_client()
    try:
        user_obj, status_code = await _fetch_szuru_user(client, login, headers)
        if user_obj is not None:
            return JSONResponse(convert_user_format(user_obj), status_code=200)

        if status_code in (401, 403):
            return JSONResponse(
                {"message": "Invalid username or password", "success": False},
                status_code=status_code,
            )

        return JSONResponse(convert_user_format({}), status_code=200)
    except httpx.RequestError as e:
        logger.error(f"Error fetching profile: {e}")
        return JSONResponse(convert_user_format({}), status_code=200)

