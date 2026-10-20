# SzuruRelay

<p align="center">
  <a href="https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12"><img src="https://img.shields.io/badge/License-EUPL%201.2-blue.svg" alt="License: EUPL 1.2"/></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.11%2B-3776AB.svg?logo=python&logoColor=white" alt="Python 3.11+"/></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi&logoColor=white" alt="FastAPI"/></a>
  <a href="https://github.com/Saetron/SzuruRelay/pkgs/container/szururelay"><img src="https://img.shields.io/badge/Docker-GHCR-2496ED.svg?logo=docker&logoColor=white" alt="Docker Container"/></a>
</p>

**SzuruRelay** is a high-performance, asynchronous translation proxy powered by **FastAPI**, **Uvicorn**, and **HTTPX**. It seamlessly translates Danbooru REST API requests into Szurubooru REST API calls and reformats responses on the fly into standard Danbooru JSON structures.

This enables popular third-party Danbooru mobile and desktop applications to connect directly to your personal or self-hosted [Szurubooru](https://github.com/rr-/szurubooru) instance without requiring custom client modifications.

---

## Architecture Overview

```
┌──────────────────────────────────────────────┐
│ Third-Party Danbooru Clients                │
│ (AnimeBoxes iOS, Boorusama, Flexbooru, etc.) │
└──────────────────────┬───────────────────────┘
                       │ Danbooru API Requests (/posts.json, /tags.json, /profile.json)
                       ▼
┌──────────────────────────────────────────────┐
│ SzuruRelay (FastAPI + ASGI + HTTPX)          │
│ • Query Syntax Translation (order:, rating:) │
│ • Model Normalization (Posts, Tags, Users)   │
│ • Streaming Media Proxy (Range / HTTP 206)   │
└──────────────────────┬───────────────────────┘
                       │ Szurubooru API Requests (/api/posts, Basic Auth)
                       ▼
┌──────────────────────────────────────────────┐
│ Szurubooru Backend Instance                  │
└──────────────────────────────────────────────┘
```

---

## Features

- **Asynchronous & Non-Blocking**: Built from the ground up on FastAPI, Starlette, and HTTPX connection pooling for lightning-fast concurrent request handling and minimal memory footprint.
- **Full Danbooru Query Syntax Translation**:
  - **Ratings**: `rating:s`, `rating:safe`, `rating:q`, `rating:questionable`, `rating:e`, `rating:explicit`, and negated queries (`-rating:e`).
  - **Sorting / Orders**: `order:score`, `order:score_asc`, `order:favcount`, `order:id`, `order:random`, `order:tagcount`, `order:date`.
  - **Favorites & Users**: `ordfav:<username>` → `fav:<username>`, `uploader:<username>` → `user:<username>`.
- **Danbooru Response Normalization**: Maps post entities, tag strings by category (`general`, `artist`, `copyright`/`series`, `character`, `meta`), user accounts, and vote statistics.
- **Media Reverse-Proxy Streaming**:
  - Built-in HTTP Range request streaming (`Range: bytes=...`, HTTP 206 Partial Content) for instant video seeking and smooth audio/video playback.
  - Path-traversal protection and automatic MIME type negotiation.
- **Flexible Media Modes**:
  - **Reverse-Proxy Mode (`REVERSE_PROXY_MODE=true`)**: Media streams directly through SzuruRelay (ideal when Szurubooru is isolated on an internal Docker network).
  - **Direct Mode (`REVERSE_PROXY_MODE=false`)**: Media URLs point directly to your public Szurubooru domain for zero proxy overhead.
- **Unified Authentication**: Supports Danbooru Basic Auth, Token Auth, query parameters, form data, and JSON credentials, automatically adapting to Szurubooru's HTTP Basic Auth.
- **Production-Ready Container**: Packaged with a slim Python 3.11 Docker container and multi-worker Uvicorn ASGI server.

---

## Tested Clients

| Client | Platform | Status | Connection Type |
|---|---|---|---|
| [**AnimeBoxes**](https://www.animebox.es/) | iOS / iPadOS | Full Support | Danbooru / Danbooru v2 |
| [**Boorusama**](https://github.com/khoadng/Boorusama) | Android / Desktop | Full Support | Danbooru |
| [**BooruHub (Flexbooru)**](https://github.com/flexbooru/flexbooru) | Android | Full Support | Danbooru |

---

## Quick Start with Docker

### 1. Using Docker Compose (Recommended)

Create or add to your `docker-compose.yml`:

```yaml
services:
  szuru-relay:
    image: ghcr.io/saetron/szururelay:latest
    container_name: szuru-relay
    ports:
      - "9000:9000"
    environment:
      # URL to your internal or external Szurubooru instance
      - SZURUBOORU_URL=http://szurubooru:8080/
      # Set to true if Szurubooru media should stream through this proxy
      - REVERSE_PROXY_MODE=false
      # Public URL of Szurubooru if REVERSE_PROXY_MODE is false
      - DOMAIN_URL=https://booru.example.com/
      - PORT=9000
    restart: unless-stopped
```

Start the service:

```bash
docker compose up -d
```

### 2. Using Docker CLI

```bash
docker run -d \
  --name szuru-relay \
  -p 9000:9000 \
  -e SZURUBOORU_URL=http://127.0.0.1:8080/ \
  -e REVERSE_PROXY_MODE=false \
  ghcr.io/saetron/szururelay:latest
```

---

## Local Development & Installation

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/Saetron/SzuruRelay.git
cd SzuruRelay

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Test Suite

```bash
pytest -v
```

### 3. Run the Server

**Development Mode (with auto-reload):**
```bash
python app.py
```

**Production ASGI Mode (Uvicorn):**
```bash
uvicorn app:app --host 0.0.0.0 --port 9000 --workers 2
```

---

## Configuration Reference

SzuruRelay follows 12-factor configuration principles: **Environment Variables** take highest precedence, followed by `config.ini` under `[API]`, falling back to safe defaults.

### Environment Variables

| Variable | `config.ini` Key | Default | Description |
|---|---|---|---|
| `SZURUBOORU_URL` | `backend_url` | `http://127.0.0.1:8080/` | Base URL of upstream Szurubooru instance |
| `PORT` | `port` | `9000` | Port on which SzuruRelay listens |
| `REVERSE_PROXY_MODE` | `reverse_proxy_mode` | `false` | When `true`, rewrites media URLs through SzuruRelay for streaming |
| `DOMAIN_URL` | `domain_url` | `""` | Public Szurubooru domain when `REVERSE_PROXY_MODE=false` |
| `ENABLE_TIMING_LOGS` | `enable_timing_logs` | `false` | Logs granular execution time breakdown for performance profiling |
| `DEBUG` | `debug` | `false` | Enables Uvicorn reload mode (development only) |

### INI File (`config.ini`)

Copy the template:
```bash
cp config_.ini config.ini
```

```ini
[API]
backend_url = http://127.0.0.1:8080/
port = 9000
reverse_proxy_mode = false
enable_timing_logs = false
```

---

## Supported Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | Health status, version, and upstream configuration |
| `/posts.json` & `/posts` | `GET` | Paginated post listing with tag search and sorting |
| `/posts/{id}.json` & `/posts/{id}` | `GET` | Detailed post metadata and variant URLs |
| `/counts/posts.json` & `/counts/posts` | `GET` | Total count of posts matching tag queries |
| `/favorites.json` & `/post_votes.json` | `GET` | Check favorite / upvote status for post IDs |
| `/favorites.json` & `/post_votes.json` | `POST` | Add a post to user favorites |
| `/favorites/{id}.json` & `/favorites/{id}` | `DELETE` | Remove a post from user favorites |
| `/tags.json` & `/tags` | `GET` | Tag search by name and category |
| `/autocomplete.json` & `/tags/autocomplete.json` | `GET` | Tag autocompletion with usage counts |
| `/users/{id}.json` & `/users.json` | `GET` | User profile details and stats |
| `/profile.json` & `/profile` | `GET` | Authenticated user profile information |
| `/data/{path:path}` | `GET` | Media byte-range streaming proxy (images & videos) |
| `/thumbnails/{path:path}` | `GET` | Thumbnail streaming proxy |
| `/avatars/{path:path}` | `GET` | User avatar streaming proxy |
| `/admin/timing/*` | `GET`, `POST` | Runtime inspection and toggles for performance metrics |

---

## Client Setup Instructions

To connect your favorite Danbooru app to SzuruRelay:

1. **Booru Type**: Select `Danbooru` (or `Danbooru v2`).
2. **Server URL**: Enter your SzuruRelay host URL (e.g. `http://your-server-ip:9000` or `https://relay.yourdomain.com`).
3. **Authentication**:
   - **Username**: Your Szurubooru username.
   - **Password / API Key**: Your Szurubooru password or API token.
4. **Done**: Browse, search, favorite, and stream media directly from your Szurubooru collection!

---

## License

This project is licensed under the **European Union Public Licence v1.2** ([EUPL-1.2](LICENSE)).
