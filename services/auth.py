import base64
import binascii
from typing import Any, Mapping, Optional, Tuple
from starlette.requests import Request
from utils import encode_auth_headers

_LOGIN_KEYS = ("login", "user", "username")
_KEY_KEYS = ("api_key", "password", "pass")


def _extract_from_mapping(
    mapping: Mapping[str, Any],
    login: Optional[str],
    api_key: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    if not login:
        for k in _LOGIN_KEYS:
            val = mapping.get(k)
            if val:
                login = str(val)
                break
    if not api_key:
        for k in _KEY_KEYS:
            val = mapping.get(k)
            if val:
                api_key = str(val)
                break
    return login, api_key


async def get_auth_headers(request: Request) -> Tuple[dict, Optional[str], Optional[str]]:
    """Extract authentication from request and return headers dict along with credentials"""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    login, api_key = await extract_auth_from_request(request)

    if login and api_key:
        # Szurubooru authenticates username and password via HTTP Basic Auth
        headers["Authorization"] = f"Basic {encode_auth_headers(login, api_key)}"

    return headers, login, api_key


async def extract_auth_from_request(request: Request) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract login and api_key/password from multiple possible sources:
    1. HTTP Basic / Token Authorization header
    2. Query string parameters (?login=...&api_key=... or ?user=...&password=...)
    3. Form data or JSON body
    """
    login: Optional[str] = None
    api_key: Optional[str] = None

    # 1. Authorization header (Basic / Token Auth)
    auth_header = request.headers.get("authorization")
    if auth_header:
        scheme, _, param = auth_header.partition(" ")
        if scheme in ("Basic", "Token") and param:
            try:
                decoded = base64.b64decode(param.strip()).decode("utf-8")
                if ":" in decoded:
                    login, _, api_key = decoded.partition(":")
            except (binascii.Error, UnicodeDecodeError, ValueError):
                pass

    # 2. Query parameters
    if (not login or not api_key) and request.query_params:
        login, api_key = _extract_from_mapping(request.query_params, login, api_key)

    # 3. Form data or JSON body
    if not login or not api_key:
        content_type = request.headers.get("content-type", "").lower()
        if "application/json" in content_type:
            try:
                json_data = await request.json()
                if isinstance(json_data, dict):
                    login, api_key = _extract_from_mapping(json_data, login, api_key)
            except Exception:
                pass
        elif "form" in content_type:
            try:
                form_data = await request.form()
                login, api_key = _extract_from_mapping(form_data, login, api_key)
            except Exception:
                pass

    return login, api_key

