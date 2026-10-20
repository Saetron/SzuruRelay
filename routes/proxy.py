import logging
import mimetypes
from urllib.parse import unquote
from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
import httpx
from config import config
from services.http_client import get_http_client

logger = logging.getLogger(__name__)
proxy_router = APIRouter()


async def _proxy_resource(
    resource_folder: str, raw_filename: str, request: Request
) -> Response:
    filename = unquote(raw_filename)

    # Path traversal protection
    if ".." in filename or filename.startswith("/"):
        return Response(content="Forbidden path", status_code=403)

    internal_url = f"{config.SZURUBOORU_URL}{resource_folder}/{filename}"

    range_header = request.headers.get("range") or request.headers.get("Range")
    headers = {}
    if range_header:
        headers["Range"] = range_header

    client = get_http_client()
    try:
        req = client.build_request("GET", internal_url, headers=headers)
        backend_resp = await client.send(req, stream=True)

        if backend_resp.status_code in (200, 206):
            content_type = backend_resp.headers.get("content-type")
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    ext = filename.lower().split("?")[0].split(".")[-1]
                    mime_map = {
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
                    content_type = mime_map.get(ext, "application/octet-stream")

            response_headers = {
                "Content-Type": content_type,
                "Cache-Control": "public, max-age=31536000",
            }

            for h in (
                "content-length",
                "content-range",
                "accept-ranges",
                "etag",
                "last-modified",
            ):
                val = backend_resp.headers.get(h)
                if val:
                    response_headers[h.title()] = val

            ext = filename.lower().split("?")[0].split(".")[-1]
            if ext in ("mp4", "webm", "avi", "mov", "mkv"):
                response_headers["Accept-Ranges"] = "bytes"

            return StreamingResponse(
                backend_resp.aiter_bytes(chunk_size=16384),
                status_code=backend_resp.status_code,
                headers=response_headers,
                media_type=content_type,
                background=backend_resp.aclose,
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
