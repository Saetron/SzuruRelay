import base64
import binascii
from typing import Tuple, Optional
from starlette.requests import Request
from utils import encode_auth_headers


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
    1. HTTP Basic Authorization header
    2. Query string parameters (?login=...&api_key=... or ?user=...&password=...)
    3. Form data (POST body)
    4. JSON body
    """
    login = None
    api_key = None

    # 1. Authorization header (Basic / Token Auth)
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth_header:
        if auth_header.startswith("Basic "):
            try:
                encoded_credentials = auth_header.split(" ", 1)[1].strip()
                decoded = base64.b64decode(encoded_credentials).decode("utf-8")
                if ":" in decoded:
                    login, api_key = decoded.split(":", 1)
            except (binascii.Error, UnicodeDecodeError, ValueError):
                pass
        elif auth_header.startswith("Token "):
            # If client forwarded a token header directly
            try:
                encoded_credentials = auth_header.split(" ", 1)[1].strip()
                decoded = base64.b64decode(encoded_credentials).decode("utf-8")
                if ":" in decoded:
                    login, api_key = decoded.split(":", 1)
            except (binascii.Error, UnicodeDecodeError, ValueError):
                pass

    # 2. Query parameters
    if not login or not api_key:
        login = (
            request.query_params.get("login")
            or request.query_params.get("user")
            or request.query_params.get("username")
            or login
        )
        api_key = (
            request.query_params.get("api_key")
            or request.query_params.get("password")
            or request.query_params.get("pass")
            or api_key
        )

    # 3. Form data or JSON body
    if not login or not api_key:
        content_type = request.headers.get("content-type", "").lower()
        if "application/json" in content_type:
            try:
                json_data = await request.json()
                if isinstance(json_data, dict):
                    login = (
                        json_data.get("login")
                        or json_data.get("user")
                        or json_data.get("username")
                        or login
                    )
                    api_key = (
                        json_data.get("api_key")
                        or json_data.get("password")
                        or json_data.get("pass")
                        or api_key
                    )
            except Exception:
                pass
        elif "form" in content_type:
            try:
                form_data = await request.form()
                login = (
                    form_data.get("login")
                    or form_data.get("user")
                    or form_data.get("username")
                    or login
                )
                api_key = (
                    form_data.get("api_key")
                    or form_data.get("password")
                    or form_data.get("pass")
                    or api_key
                )
            except Exception:
                pass

    return login, api_key
