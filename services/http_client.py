from typing import Optional
import httpx

# Reusable HTTP client instance
_client: Optional[httpx.AsyncClient] = None


def get_http_client() -> httpx.AsyncClient:
    """Get or create the global AsyncClient for upstream requests"""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=25, max_connections=50),
            follow_redirects=True,
        )
    return _client


async def close_http_client():
    """Close the global AsyncClient on application shutdown"""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        _client = None
