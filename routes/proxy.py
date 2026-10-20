import logging
import mimetypes
from urllib.parse import unquote
from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
import httpx
from config import config
from services.http_client import get_http_client

logger = logging.getLogger(__name__)
proxy_router = APIRouter()

_MIME_MAP = {
    "mp4": "video/mp4",
    "webm": "video/webm",
    "avi": "video/avi",
    "mov": "video/quicktime",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
}

_VIDEO_EXTS = ("mp4", "webm", "avi", "mov", "mkv")

_FORWARDED_HEADERS = (
    ("content-length", "Content-Length"),
    ("content-range", "Content-Range"),
    ("accept-ranges", "Accept-Ranges"),
    ("etag", "Etag"),
    ("last-modified", "Last-Modified"),
)


async def _proxy_resource(
    resource_folder: str, raw_filename: str, request: Request
) -> Response:
    filename = unquote(raw_filename)

    # Path traversal protection
    if (
        ".." in filename
        or filename.startswith("/")
        or "\\" in filename
        or "\x00" in filename
    ):
        return Response(content="Forbidden path", status_code=403)

    internal_url = f"{config.SZURUBOORU_URL}{resource_folder}/{filename}"

    range_header = request.headers.get("range")
    headers = {"Range": range_header} if range_header else {}

    client = get_http_client()
    try:
        req = client.build_request("GET", internal_url, headers=headers)
        backend_resp = await client.send(req, stream=True)

        if backend_resp.status_code in (200, 206):
            ext = filename.lower().partition("?")[0].rsplit(".", 1)[-1]
            content_type = backend_resp.headers.get("content-type")
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = _MIME_MAP.get(ext, "application/octet-stream")

            response_headers = {
                "Content-Type": content_type,
                "Cache-Control": "public, max-age=31536000",
            }

            for header_key, header_title in _FORWARDED_HEADERS:
                val = backend_resp.headers.get(header_key)
                if val:
                    response_headers[header_title] = val

            if ext in _VIDEO_EXTS:
                response_headers["Accept-Ranges"] = "bytes"

            return StreamingResponse(
                backend_resp.aiter_bytes(chunk_size=16384),
                status_code=backend_resp.status_code,
                headers=response_headers,
                media_type=content_type,
                background=BackgroundTask(backend_resp.aclose),
            )
        else:
            await backend_resp.aclose()
            return Response(content="File not found", status_code=404)

    except httpx.RequestError as e:
        logger.error(f"Proxy error for {resource_folder}/{filename}: {e}")
        return Response(content="Internal server error", status_code=500)


@proxy_router.get("/data/{filename:path}")
async def proxy_content(filename: str, request: Request):
    """Proxy image and video content with HTTP range support"""
    return await _proxy_resource("data", filename, request)


@proxy_router.get("/thumbnails/{filename:path}")
async def proxy_thumbnail(filename: str, request: Request):
    """Proxy image thumbnails"""
    return await _proxy_resource("thumbnails", filename, request)


@proxy_router.get("/avatars/{filename:path}")
async def proxy_avatar(filename: str, request: Request):
    """Proxy user avatars"""
    return await _proxy_resource("avatars", filename, request)

