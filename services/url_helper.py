from typing import Optional
from urllib.parse import urljoin
from starlette.requests import Request
from config import config


def get_current_domain(request: Optional[Request] = None) -> str:
    """Dynamically get the base URL of the current request or configured domain"""
    if config.REVERSE_PROXY_MODE and request:
        scheme = request.headers.get("x-forwarded-proto") or request.url.scheme
        host = (
            request.headers.get("x-forwarded-host")
            or request.headers.get("host")
            or request.url.netloc
        )
        return f"{scheme}://{host}/"
    return config.DOMAIN_URL


def build_resource_url(
    resource_path: str,
    request: Optional[Request] = None,
    base_domain: Optional[str] = None,
) -> str:
    """Build full resource URL cleanly without double slashes"""
    if not resource_path:
        return ""

    if resource_path.startswith(("http://", "https://")):
        return resource_path

    base = base_domain or get_current_domain(request)
    clean_path = resource_path.lstrip("/")
    if not base:
        return clean_path
    return f"{base}{clean_path}" if base.endswith("/") else urljoin(base, clean_path)

