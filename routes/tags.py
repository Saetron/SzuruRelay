import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import httpx
from config import config
from services.auth import get_auth_headers
from models.converters import category_map
from services.http_client import get_http_client

logger = logging.getLogger(__name__)
tags_router = APIRouter()


def _get_tag_category_num(cat_raw) -> int:
    if isinstance(cat_raw, int):
        return cat_raw
    cat_str = str(cat_raw).lower()
    return category_map.get(cat_str, 0)


@tags_router.get("/tags/autocomplete.json")
@tags_router.get("/tags/autocomplete")
@tags_router.get("/autocomplete.json")
@tags_router.get("/autocomplete")
async def autocomplete_tags(request: Request):
    headers, _, _ = await get_auth_headers(request)

    query = (
        request.query_params.get("search[query]")
        or request.query_params.get("search[name_matches]")
        or request.query_params.get("term")
        or request.query_params.get("q")
        or ""
    ).strip()

    if query:
        if len(query) < 3:
            search_pattern = f"{query}*"
        else:
            search_pattern = f"*{query}*"
    else:
        search_pattern = "*"

    try:
        limit = min(int(request.query_params.get("limit", 10)), 50)
    except (ValueError, TypeError):
        limit = 10

    client = get_http_client()
    try:
        response = await client.get(
            f"{config.SZURUBOORU_API_URL}/tags",
            params={"query": f"{search_pattern} sort:usages", "limit": limit},
            headers=headers,
            timeout=10.0,
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            auto_complete_tags = []
            for tag in results:
                names = tag.get("names", [])
                if not names:
                    continue
                tag_name = names[0]
                category_num = _get_tag_category_num(tag.get("category", "default"))
                auto_complete_tags.append(
                    {
                        "type": "tag-word",
                        "label": tag_name,
                        "value": tag_name,
                        "category": category_num,
                        "post_count": tag.get("usages", 0),
                    }
                )
            return JSONResponse(auto_complete_tags, status_code=200)
        else:
            return JSONResponse(
                {"message": "Failed to fetch tags"},
                status_code=response.status_code,
            )
    except httpx.RequestError as e:
        logger.error(f"Error autocompleting tags: {e}")
        return JSONResponse([], status_code=200)


@tags_router.get("/tags.json")
@tags_router.get("/tags")
async def search_tags(request: Request):
    headers, _, _ = await get_auth_headers(request)

    name_query = (
        request.query_params.get("search[name_matches]")
        or request.query_params.get("search[name]")
        or request.query_params.get("name")
        or ""
    ).strip()

    try:
        limit = min(int(request.query_params.get("limit", 20)), 100)
    except (ValueError, TypeError):
        limit = 20

    query_str = f"{name_query} sort:usages" if name_query else "sort:usages"

    client = get_http_client()
    try:
        response = await client.get(
            f"{config.SZURUBOORU_API_URL}/tags",
            params={"query": query_str, "limit": limit},
            headers=headers,
            timeout=10.0,
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            tags_list = []
            for i, tag in enumerate(results):
                names = tag.get("names", [])
                tag_name = names[0] if names else ""
                category_num = _get_tag_category_num(tag.get("category", "default"))
                tags_list.append(
                    {
                        "id": i + 1,
                        "name": tag_name,
                        "post_count": tag.get("usages", 0),
                        "category": category_num,
                        "is_locked": False,
                        "created_at": "2020-01-01T00:00:00Z",
                        "updated_at": "2020-01-01T00:00:00Z",
                    }
                )
            return JSONResponse(tags_list, status_code=200)
        else:
            return JSONResponse([], status_code=response.status_code)
    except httpx.RequestError as e:
        logger.error(f"Error fetching tags: {e}")
        return JSONResponse([], status_code=200)
