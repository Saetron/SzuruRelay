# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.1.1] - 2026-10-21

### Changed
- **Dependency Upgrades**:
  - Upgraded `fastapi` to `>=0.143.3`.
  - Upgraded `uvicorn[standard]` to `>=0.54.0`.
  - Upgraded `python-multipart` to `>=0.0.32`.
  - Upgraded `pytest` to `>=9.1.1`.
  - Upgraded `pytest-asyncio` to `>=1.4.0`.
- **Docker Base Image**: Updated `Dockerfile` base image from `python:3.11-slim` to `python:3.15-slim`.
- **GitHub Actions Workflows**: Upgraded CI/CD actions in `docker-build.yml`:
  - `actions/checkout` to `v7`
  - `actions/setup-python` to `v7`
  - `docker/login-action` to `v4`
  - `docker/metadata-action` to `v6`
  - `docker/build-push-action` to `v7`

### Added
- **Project Acknowledgements**: Added attribution to [MILES-FAN](https://github.com/MILES-FAN) and the original `Szuru-Dan` project in `README.md`.

---

## [2.1.0] - 2026-10-20

### Added
- **Configurable Release Workflow**: Added `bump_type` (`none`, `patch`, `minor`, `major`, default `none`) input to the GitHub Actions Docker release workflow (`.github/workflows/docker-build.yml`) so manual `VERSION` updates are respected without forced auto-incrementing.
- **Path Suffix Utility**: Added `strip_json_suffix()` in `utils.py` using `str.removesuffix(".json")` to standardize `.json` path parameter handling across routes.
- **Async Timing Decorator**: Extended `timing_decorator` in `services/timing.py` to support both synchronous and `async` coroutine functions.

### Changed
- **Concurrent Favorite Lookups**: Optimized `GET /favorites.json` (`routes/favorites.py`) to query multiple post IDs concurrently via `asyncio.gather` instead of sequentially awaiting each upstream request.
- **Single-Pass Post Tag Conversion**: Refactored `convert_post_format` (`models/converters.py`) to categorize tags and build `tag_string` in a single loop, eliminating redundant tag iterations and per-post `Timer` overhead.
- **Batch Domain Resolution**: Pre-computed `base_domain` once per post search batch in `routes/posts.py` rather than re-evaluating request headers twice per post.
- **High-Resolution Monotonic Timers**: Switched `Timer` and `RequestTimer` (`services/timing.py`) to `time.perf_counter()`, added `__slots__`, and bypassed clock syscalls completely when timing logs are disabled.
- **Pre-Allocated Lookup & Translation Tables**: Hoisted rating, sort, and MIME dictionaries as well as `str.maketrans` tables to module-level constants in `utils.py`, `routes/favorites.py`, and `routes/proxy.py`.
- **Deduplicated User & Auth Logic**: Consolidated user lookup with search fallback (`_fetch_szuru_user`) in `routes/users.py`, credential extraction in `services/auth.py`, and configuration parsing helpers in `config.py`.

### Fixed
- **Streaming Response Cleanup**: Wrapped `backend_resp.aclose` in Starlette `BackgroundTask` inside `routes/proxy.py` so upstream HTTP streams close cleanly without raising a `TypeError` after streaming completes.
- **Proxy Path Traversal Hardening**: Rejected backslashes (`\`) and null bytes (`\x00`) in addition to `..` and leading slashes in `routes/proxy.py`.

---

## [0.2.1] - 2026-10-20

### Changed
- Updated Docker image references in documentation to `ghcr.io/saetron/szururelay:latest` and removed legacy README banner.

---

## [0.2.0] - 2026-10-20

### Added
- **FastAPI & ASGI Architecture**: Rebuilt the core proxy application on FastAPI and Uvicorn for asynchronous non-blocking I/O and low memory overhead.
- **Async HTTP Client**: Introduced shared `httpx.AsyncClient` with connection pooling (`services/http_client.py`) and graceful shutdown lifecycle management.
- **Streaming Reverse-Proxy**: Upgraded `/data/*`, `/thumbnails/*`, and `/avatars/*` media streaming using Starlette `StreamingResponse` and async chunk streaming with HTTP 206 Partial Content (`Range` requests) support.
- **Flexible Path Parameter Parsing**: Added automatic handling and normalization of `.json` extensions in URL path parameters (e.g. `/posts/{id}.json`, `/favorites/{id}.json`, `/users/{id}.json`).
- **Comprehensive Test Suite**: Migrated tests to `fastapi.testclient.TestClient` and `AsyncMock`, expanding test coverage to 24 test cases across routes, query parsers, and model converters.
- **Contributor & Agent Documentation**: Added [AGENTS.md](AGENTS.md) documenting architecture, query translation specifications, and development rules.
- **Overhauled README**: Added architecture flowcharts, mobile client configuration guide, and endpoint matrix.

### Changed
- **Project Rebranding**: Rebranded project from `Szuru-Dan` to **`SzuruRelay`** with updated container definitions (`ghcr.io/saetron/szururelay`) and repository remotes.
- **Docker Release Trigger**: Updated GitHub Actions build workflow to trigger on manual dispatch (`workflow_dispatch`) rather than automatic branch pushes.
- **Dependencies**: Replaced `Flask` and `gunicorn` with `fastapi`, `uvicorn[standard]`, `httpx`, and `python-multipart`.

---

## [0.1.6] - 2026-09-18

### Fixed
- **Authentication Mapping**: Mapped Danbooru `api_key` to password via HTTP Basic Auth header (`Authorization: Basic ...`) required by Szurubooru.
- **User Profile Fetching**: Enhanced profile endpoint to attempt direct user lookups before falling back to user searches.

---

## [0.1.5] - 2026-09-18

### Changed
- Removed legacy `pre-commit` configuration and pre-commit GitHub Actions workflow.

---

## [0.1.4] - 2026-09-18

### Changed
- Refined language and formatting in `LICENSE` file.

---

## [0.1.3] - 2026-09-18

### Added
- **Automated Tests**: Introduced unit tests for query parsing, rating conversions, tag processing, and route integration tests using `pytest`.
- **Danbooru Query Parsing**: Added token translation for search filters (`rating:s/q/e`, `order:score`, `ordfav:<user>`, `uploader:<user>`).

### Changed
- **Relicensed**: Relicensed project under the **European Union Public Licence v1.2** (EUPL-1.2).
- Overhauled post and tag normalization schemas for full compatibility with mobile clients (AnimeBoxes, Boorusama, Flexbooru).

---

## [0.1.2] - 2026-08-22

### Fixed
- Fixed GitHub Actions permissions for publishing packages to GitHub Container Registry (GHCR).

---

## [0.1.1] - 2026-08-22

### Added
- Automated Docker image build and release workflow via GitHub Actions.
- Production `Dockerfile` and `docker-compose.yml`.

---

## [0.1.0] - 2026-08-23

### Added
- Initial modularized project structure with `routes/`, `services/`, and `models/`.
- Built-in reverse proxy mode for static media resources with video streaming support.
- 12-factor configuration support via environment variables and `config.ini`.
