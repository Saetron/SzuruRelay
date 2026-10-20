# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
