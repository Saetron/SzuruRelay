import logging
from typing import Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import httpx
from config import config
from services.auth import get_auth_headers
from models.converters import convert_post_format
from utils import parse_query
from services.timing import Timer, RequestTimer
from services.http_client import get_http_client

logger = logging.getLogger(__name__)
posts_router = APIRouter()


@posts_router.get("/posts")
@posts_router.get("/posts.json")
async def search_posts(request: Request):
    timer = RequestTimer("search_posts")
    timer.checkpoint("Request started")

    # Parse query parameters safely
    with Timer("Parse query parameters"):
        raw_query = request.query_params.get("tags", "")
        query = parse_query(raw_query)

        # Parse limit
        try:
            raw_limit = request.query_params.get("limit", "40")
            limit = max(1, min(int(raw_limit), 100))
        except (ValueError, TypeError):
            limit = 40

        # Parse page
        raw_page = request.query_params.get("page", "1")
        try:
            page = int(raw_page)
            if page < 1:
                page = 1
        except (ValueError, TypeError):
            page = 1

    timer.checkpoint("Query parameters parsed")

    with Timer("Get authentication headers"):
        headers, login, _ = await get_auth_headers(request)

    timer.checkpoint("Authentication processed")

    offset = (page - 1) * limit
    api_url = f"{config.SZURUBOORU_API_URL}/posts"
    params = {
        "offset": offset,
        "limit": limit,
        "query": query,
    }

    timer.checkpoint("API request prepared")

    client = get_http_client()
    with Timer("Szurubooru API request"):
        try:
            response = await client.get(api_url, params=params, headers=headers, timeout=30.0)
        except httpx.TimeoutException:
            logger.error(f"API request timeout for query: {raw_query}")
            return JSONResponse({"message": "API request timeout"}, status_code=504)
        except httpx.RequestError as e:
            logger.error(f"API request failed: {e}")
            return JSONResponse({"message": "API request failed"}, status_code=500)

    timer.checkpoint("Szurubooru API response received")

    if response.status_code == 200:
        with Timer("Parse JSON response"):
            try:
                szuru_posts = response.json()
            except ValueError:
                return JSONResponse([], status_code=200)

        timer.checkpoint("JSON parsed")

        with Timer("Convert post formats"):
            results = szuru_posts.get("results", [])
            danbooru_posts = []

            for post in results:
                converted_post = convert_post_format(
                    post, login=login, request=request
                )
                danbooru_posts.append(converted_post)

        timer.checkpoint("All posts converted")
        timer.summary()

        return JSONResponse(danbooru_posts, status_code=200)
    else:
        timer.checkpoint(f"API error: {response.status_code}")
        timer.summary()
        return JSONResponse({"message": "Failed to fetch posts"}, status_code=response.status_code)


@posts_router.get("/posts/{post_id}.json")
@posts_router.get("/posts/{post_id}")
async def get_post(post_id: str, request: Request):
    clean_id = post_id[:-5] if post_id.endswith(".json") else post_id
    try:
        pid = int(clean_id)
    except ValueError:
        return JSONResponse({"message": "Invalid post ID"}, status_code=400)

    timer = RequestTimer(f"post-{pid}")
    timer.checkpoint("Single post request started")

    with Timer("Get authentication headers"):
        headers, login, _ = await get_auth_headers(request)

    timer.checkpoint("Authentication processed")

    client = get_http_client()
    with Timer("Szurubooru API request"):
        try:
            response = await client.get(
                f"{config.SZURUBOORU_API_URL}/post/{pid}",
                headers=headers,
                timeout=20.0,
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to fetch post {pid}: {e}")
            return JSONResponse({"message": "API request failed"}, status_code=500)

    timer.checkpoint("API response received")

    if response.status_code == 200:
        with Timer("Parse JSON and convert format"):
            szuru_post = response.json()
            danbooru_post = convert_post_format(
                szuru_post, login=login, request=request
            )

        timer.checkpoint("Post converted")
        timer.summary()

        return JSONResponse(danbooru_post, status_code=200)
    else:
        timer.checkpoint(f"API error: {response.status_code}")
        timer.summary()
        return JSONResponse({"message": "Post not found"}, status_code=response.status_code)


@posts_router.get("/counts/posts.json")
@posts_router.get("/counts/posts")
async def get_post_count(request: Request):
    raw_query = request.query_params.get("tags", "")
    query = parse_query(raw_query)
    headers, _, _ = await get_auth_headers(request)

    client = get_http_client()
    try:
        response = await client.get(
            f"{config.SZURUBOORU_API_URL}/posts",
            params={"offset": 0, "limit": 1, "query": query},
            headers=headers,
            timeout=10.0,
        )
        if response.status_code == 200:
            data = response.json()
            total = data.get("total", 0)
            return JSONResponse({"counts": {"posts": total}}, status_code=200)
    except httpx.RequestError as e:
        logger.warning(f"Failed to fetch post count: {e}")

    return JSONResponse({"counts": {"posts": 0}}, status_code=200)
