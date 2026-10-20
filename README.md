# Szuru-Dan Docker

[![License: EUPL 1.2](https://img.shields.io/badge/License-EUPL%201.2-blue.svg)](https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12)

A production-ready API translation proxy that maps Szurubooru API endpoints into Danbooru-style responses, allowing third-party Danbooru mobile and desktop clients to connect directly to your Szurubooru server.

---

## Features

- **Danbooru Compatibility**: Maps Danbooru requests to Szurubooru queries including ratings (`rating:s/q/e`), sort orders (`order:score`, `order:favcount`, `order:id`), and tags.
- **Client Support**: Validated with [AnimeBoxes](https://www.animebox.es/) (iOS), [Boorusama](https://github.com/khoadng/Boorusama) (Android/Desktop), and [BooruHub / Flexbooru](https://github.com/flexbooru/flexbooru) (Android).
- **Reverse Proxy Media Streaming**: Built-in HTTP range request proxying for fast image loading and video streaming.
- **12-Factor Configuration**: Configure via environment variables or `config.ini`.
- **Production ASGI Server**: Powered by FastAPI, Uvicorn, and async HTTPX connection pooling.

---

## Getting Started

### Option 1: Running with Docker (Recommended)

#### 1. Using Docker Compose
Create a `docker-compose.yml` file:

```yaml
services:
  szuru-dan:
    image: ghcr.io/saetron/szuru-dan-docker:latest
    container_name: szuru-dan
    ports:
      - "9000:9000"
    environment:
      - SZURUBOORU_URL=http://127.0.0.1:8080/
      - REVERSE_PROXY_MODE=false
      - PORT=9000
    restart: unless-stopped
```

Start the container:

```bash
docker compose up -d
```

#### 2. Using Docker CLI

```bash
docker run -d \
  --name szuru-dan \
  -p 9000:9000 \
  -e SZURUBOORU_URL=http://127.0.0.1:8080/ \
  -e REVERSE_PROXY_MODE=false \
  ghcr.io/saetron/szuru-dan-docker:latest
```

### Option 2: Local Installation

#### 1. Clone the repository
```bash
git clone https://github.com/Saetron/Szuru-Dan-Docker.git
cd Szuru-Dan-Docker
```

#### 2. Install dependencies
```bash
pip install -r requirements.txt
```

#### 3. Run the server
```bash
python app.py
# Or directly with Uvicorn:
uvicorn app:app --host 0.0.0.0 --port 9000 --workers 2
```

---

## Configuration

You can configure Szuru-Dan using **Environment Variables** (recommended for Docker) or a `config.ini` file:

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SZURUBOORU_URL` | `http://127.0.0.1:8080/` | Base URL of your Szurubooru instance |
| `PORT` | `9000` | Port on which Szuru-Dan listens |
| `REVERSE_PROXY_MODE` | `false` | When true, image/thumbnail URLs point to this proxy server |
| `DOMAIN_URL` | `""` | Custom public domain URL if not using reverse proxy mode |
| `ENABLE_TIMING_LOGS` | `false` | Logs performance timing metrics for debugging |
| `DEBUG` | `false` | Enable Flask debug mode (development only) |

### INI File (`config.ini`)
Copy `config_.ini` to `config.ini`:
```ini
[API]
backend_url = http://127.0.0.1:8080/
port = 9000
reverse_proxy_mode = false
enable_timing_logs = false
```

---

## Supported Endpoints

- `/health` - Health check endpoint
- `/posts.json` & `/posts` - Post search with pagination and tag filtering
- `/posts/{id}.json` - Single post details
- `/counts/posts.json` - Post counts matching tag queries
- `/favorites.json` & `/post_votes.json` - View, add (`POST`), and remove (`DELETE`) user favorites
- `/tags.json` - Tag list and search
- `/tags/autocomplete.json` & `/autocomplete.json` - Fast tag autocompletion
- `/users/{id}.json` & `/users.json` - User profile queries
- `/profile.json` - Current user profile
- `/data/<path>`, `/thumbnails/<path>`, `/avatars/<path>` - Media proxying with HTTP byte-range streaming

---

## Tested Clients

- **iOS**: [AnimeBoxes](https://www.animebox.es/)
- **Android / Desktop**: [Boorusama](https://github.com/khoadng/Boorusama)
- **Android**: [BooruHub (Flexbooru)](https://github.com/flexbooru/flexbooru)

---

## License

This project is licensed under the **European Union Public Licence v1.2** ([EUPL-1.2](LICENSE)).
