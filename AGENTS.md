# AGENTS.md — Contributor & AI Agent Guide for Szuru-Dan

## 1. Project Overview & Architecture

**Szuru-Dan** is a production-ready API translation proxy written in Python (Flask + Gunicorn). It translates Danbooru REST API requests into Szurubooru REST API calls and converts responses back into Danbooru-compatible formats.

This allows third-party Danbooru client applications (such as **AnimeBoxes** on iOS, **Boorusama** on Android/Desktop, and **BooruHub / Flexbooru** on Android) to connect directly to personal or self-hosted Szurubooru instances.

### Key Capabilities
- **Query & Filter Translation**: Translates Danbooru query syntax (ratings, order/sorting, favorites, uploaders) into Szurubooru syntax.
- **Model Normalization**: Maps Szurubooru posts, categories, tags, and user profiles into standard Danbooru JSON formats.
- **Media Reverse-Proxy**: Optional streaming reverse-proxy with HTTP byte-range request support (`Range: bytes=...`, HTTP 206) for video scrubbing and fast image loading.
- **Dual Configuration**: 12-Factor environment variables with fallback to `config.ini`.
- **Production WSGI**: Multi-threaded deployment using Gunicorn with connection pooling via `urllib3` / `requests.adapters.HTTPAdapter`.

---

## 2. Repository Layout

```
Szuru-Dan-Docker/
├── app.py                      # Application factory (create_app), ProxyFix WSGI middleware, /health route
├── config.py                   # Configuration management (environment variables & config.ini)
├── config_.ini                 # Template INI configuration file
├── Dockerfile                  # Production container definition (Python 3.11-slim, Gunicorn)
├── docker-compose.yml          # Docker Compose configuration sample
├── requirements.txt            # Python dependencies (Flask, requests, gunicorn, pytest)
├── pytest.ini                  # Pytest test discovery settings
├── VERSION                     # Semantic version tracking file
├── models/
│   └── converters.py           # Converters for posts, tags, users, ratings, and categories
├── routes/
│   ├── __init__.py             # Route package marker
│   ├── admin.py                # Admin endpoints (/admin/timing/*)
│   ├── favorites.py            # Favorites & votes (/favorites.json, /post_votes.json)
│   ├── posts.py                # Post searches and counts (/posts.json, /counts/posts.json)
│   ├── proxy.py                # Media byte-range streaming proxy (/data, /thumbnails, /avatars)
│   ├── tags.py                 # Tag search and autocomplete (/tags.json, /autocomplete.json)
│   └── users.py                # User profiles (/users.json, /profile.json)
├── services/
│   ├── auth.py                 # Authentication extraction & Basic Auth conversion
│   ├── timing.py               # Request performance profiling and timing logs
│   └── url_helper.py           # Media URL construction (reverse proxy vs direct URL)
├── tests/
│   ├── test_converters.py      # Unit tests for data conversions
│   ├── test_routes.py          # Integration tests for Flask endpoints and auth handling
│   └── test_utils.py           # Unit tests for query parsing, rating mapping, and tags
└── utils.py                    # Query parsing, rating conversion, tag utilities
```

---

## 3. Core API Translation & Specifications

### 3.1 Search Query Syntax Translation (`utils.py:parse_query`)

| Danbooru Syntax | Szurubooru Translated Syntax | Description |
|---|---|---|
| `rating:s`, `rating:safe`, `rating:g` | `safety:safe` | Safe rating |
| `rating:q`, `rating:questionable`, `rating:sensitive` | `safety:sketchy` | Questionable / Sketchy rating |
| `rating:e`, `rating:explicit`, `rating:unsafe` | `safety:unsafe` | Explicit rating |
| `-rating:e` | `-safety:unsafe` | Negation operator preserved |
| `order:score`, `order:score_desc` | `sort:score` | Order by score descending |
| `order:score_asc` | `sort:score-asc` | Order by score ascending |
| `order:favcount`, `order:fav` | `sort:favs` | Order by favorite count |
| `order:id`, `order:id_desc` | `sort:id` | Order by post ID descending |
| `order:id_asc` | `sort:id-asc` | Order by post ID ascending |
| `order:random`, `order:rank` | `sort:random` | Random post order |
| `order:tagcount`, `order:tag_count` | `sort:tag-count` | Order by tag count |
| `order:date` | `sort:creation-date` | Order by creation date |
| `ordfav:<username>` | `fav:<username>` | Posts favorited by user |
| `uploader:<username>` | `user:<username>` | Posts uploaded by user |

### 3.2 Tag Category Mapping (`models/converters.py`)

| Category Name | Danbooru Category ID | Szurubooru Category |
|---|---|---|
| `general`, `default` | `0` | General |
| `artist` | `1` | Artist |
| `copyright`, `series` | `3` | Series / Copyright |
| `character` | `4` | Character |
| `meta` | `5` | Meta |

### 3.3 User Rank Mapping (`models/converters.py`)

| Szurubooru Rank | Danbooru Level | Level String |
|---|---|---|
| `anonymous` | `0` | Anonymous |
| `restricted` | `10` | Restricted |
| `regular` | `20` | Member |
| `power` | `30` | Gold |
| `moderator` | `40` | Moderator |
| `administrator` | `50` | Admin |

### 3.4 Authentication Mechanism (`services/auth.py`)

Danbooru clients provide credentials through:
1. `Authorization: Basic base64(login:api_key)`
2. `Authorization: Token base64(login:api_key)`
3. Query parameters (`?login=...&api_key=...` or `?user=...&password=...`)
4. Form body or JSON body parameters.

Szurubooru requires HTTP Basic Auth: `Authorization: Basic base64(username:password_or_token)`. `services/auth.py` standardizes all incoming methods and sends the appropriate HTTP Basic Auth header upstream.

---

## 4. Configuration Reference

Configuration is managed in `config.py` using cascading priority: **Environment Variables** take precedence, followed by `config.ini` (under `[API]`), falling back to built-in defaults.

| Environment Variable | INI Key (`[API]`) | Default | Description |
|---|---|---|---|
| `SZURUBOORU_URL` | `backend_url` | `http://127.0.0.1:8080/` | Base URL of Szurubooru instance |
| `PORT` | `port` | `9000` | Port for the Szuru-Dan proxy |
| `REVERSE_PROXY_MODE` | `reverse_proxy_mode` | `false` | When `true`, media URLs point back to this proxy for streaming |
| `DOMAIN_URL` | `domain_url` | `""` | Custom domain if not reverse proxying (falls back to `SZURUBOORU_URL`) |
| `ENABLE_TIMING_LOGS` | `enable_timing_logs` | `false` | Logs performance timing metrics for profiling |
| `DEBUG` | `debug` | `false` | Enables Flask debug mode (development only) |

---

## 5. Development & Testing Commands

### Setup Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running Tests
All tests are implemented with `pytest`:
```bash
pytest
```

Run specific test modules:
```bash
pytest tests/test_utils.py
pytest tests/test_converters.py
pytest tests/test_routes.py
```

### Running the Application

**Development Server:**
```bash
python app.py
```

**Production WSGI Server (Gunicorn):**
```bash
gunicorn -w 2 -k gthread --threads 4 -b 0.0.0.0:9000 "app:create_app()"
```

**Docker Build & Run:**
```bash
docker build -t szuru-dan .
docker run -p 9000:9000 -e SZURUBOORU_URL=http://host.docker.internal:8080/ szuru-dan
```

---

## 6. Release & CI/CD Pipeline

The GitHub Actions workflow at [`.github/workflows/docker-build.yml`](.github/workflows/docker-build.yml) manages automated build and packaging:

- **Trigger**: Manual trigger only via `workflow_dispatch`.
- **Workflow Steps**:
  1. Checks out repository with full git history (`fetch-depth: 0`).
  2. Sets up Python 3.11, installs `requirements.txt`, and runs test suite (`pytest`).
  3. Automatically bumps patch version in `VERSION`.
  4. Commits `VERSION` with message `chore(release): bump version to X.Y.Z [skip ci]`.
  5. Creates and pushes git tag `vX.Y.Z`.
  6. Builds multi-platform Docker image and pushes to GitHub Container Registry (`ghcr.io/saetron/szuru-dan-docker`).
  7. Tags Docker images with `:latest`, `:X.Y.Z`, and semver patterns.

---

## 7. Guidelines for AI Agents & Contributors

1. **Client Compatibility is Paramount**:
   - Do not alter the Danbooru JSON response schema without verifying that mobile clients (AnimeBoxes, Boorusama, Flexbooru) support the change.
   - Return sensible defaults (e.g. empty lists or anonymous user structures) rather than raising unhandled exceptions or returning HTTP 500 when upstream fields are missing.

2. **Security & Proxy Boundaries**:
   - In `routes/proxy.py`, always ensure path traversal sequences (`..`) and malicious character sequences are rejected with HTTP 403/404.
   - Never log or expose raw passwords, API keys, or Basic Auth secrets in logs or error traces.

3. **Modifying Converters or Parsing**:
   - Any modifications to `models/converters.py` or `utils.py` must be accompanied by new or updated unit tests in `tests/test_converters.py` or `tests/test_utils.py`.
   - Ensure all `pytest` suites pass before finalizing commits.

4. **Blueprint Architecture**:
   - Keep route endpoints in their corresponding `routes/*.py` blueprint modules.
   - Keep translation logic in `models/converters.py` and helper functions in `services/` or `utils.py`.
   - Register any new blueprints inside `create_app()` in `app.py`.
