import configparser
import os
from pathlib import Path


class Config:
    _TRUTHY = ("true", "1", "yes")

    def __init__(self, config_path: str = "config.ini"):
        parser = configparser.ConfigParser()
        ini_file = Path(config_path)
        if ini_file.exists():
            parser.read(config_path)

        self._api = parser["API"] if "API" in parser else {}

        # 1. Szurubooru backend URL
        backend_url = self._get_str("SZURUBOORU_URL", "backend_url", "http://127.0.0.1:8080/")
        if not backend_url.endswith("/"):
            backend_url += "/"
        self.SZURUBOORU_URL = backend_url

        # API base endpoint
        if self.SZURUBOORU_URL.endswith("/api/"):
            self.SZURUBOORU_API_URL = self.SZURUBOORU_URL[:-1]
        elif self.SZURUBOORU_URL.endswith("/api"):
            self.SZURUBOORU_API_URL = self.SZURUBOORU_URL
        else:
            self.SZURUBOORU_API_URL = f"{self.SZURUBOORU_URL}api"

        # 2. Reverse proxy mode
        self.REVERSE_PROXY_MODE = self._get_bool("REVERSE_PROXY_MODE", "reverse_proxy_mode", False)

        # 3. Enable timing logs
        self.ENABLE_TIMING_LOGS = self._get_bool("ENABLE_TIMING_LOGS", "enable_timing_logs", False)

        # 4. Domain URL for ordinary mode
        if not self.REVERSE_PROXY_MODE:
            domain = self._get_str("DOMAIN_URL", "domain_url", "")
            if domain and not domain.endswith("/"):
                domain += "/"
            self.DOMAIN_URL = domain or self.SZURUBOORU_URL
        else:
            self.DOMAIN_URL = ""

        # 5. Service Port
        self.SERVICE_PORT = self._get_int("PORT", "port", 9000)

        # 6. Debug mode
        self.DEBUG = self._get_bool("DEBUG", "debug", False)

    def _get_str(self, env_key: str, ini_key: str, default: str) -> str:
        return os.environ.get(env_key, self._api.get(ini_key, default))

    def _get_bool(self, env_key: str, ini_key: str, default: bool) -> bool:
        raw = os.environ.get(env_key)
        if raw is None:
            raw = self._api.get(ini_key, str(default))
        return raw.strip().lower() in self._TRUTHY

    def _get_int(self, env_key: str, ini_key: str, default: int) -> int:
        raw = os.environ.get(env_key) or self._api.get(ini_key)
        if raw is not None:
            try:
                return int(raw)
            except (ValueError, TypeError):
                pass
        return default


# Global config instance
config = Config()

