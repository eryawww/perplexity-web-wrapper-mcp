# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Unofficial Perplexity AI client — CLI, MCP server, Python library, and FastAPI server. Works without the official API by using browser cookie authentication with automatic Playwright-based login.

## Commands

```bash
# Install
uv sync && uv run playwright install chromium

# CLI
uv run perplexity search "query" --mode auto|pro|reasoning|"deep research"
uv run perplexity login

# MCP server (stdio)
uv run mcp_server.py

# FastAPI server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

No test suite or linter is configured.

## Architecture

### Four interfaces, one core

1. **`lib/perplexity.Client`** — Core client. Manages a `curl-cffi` session, constructs requests to `perplexity.ai`, parses SSE responses. All other interfaces wrap this.

2. **`cli.py`** — CLI entry point (`uv run perplexity`). Argparse-based, covers all Client methods.

3. **`mcp_server.py`** — MCP server (stdio transport, FastMCP). 11 tools: `search`, `get_threads`, `get_thread`, `discover_feed`, `list_spaces`, `get_space`, `create_space`, `edit_space`, `delete_space`, `add_space_link`, `list_space_threads`.

4. **`api/main.py`** — FastAPI app with SSE streaming and sync endpoints.

### Auth flow (`lib/auth.py`)

On `Client.__init__`, validates session by hitting `/rest/thread/list_ask_threads`. If unauthenticated, launches a headed Chrome browser via Playwright+stealth for manual login. Cookies persist to `perplexity_cookies.json` after every API call. Persistent browser profile in `.browser_profile/`.

### Response flow

Client POSTs to `/rest/sse/perplexity_ask`, receives `event: message` / `event: end_of_stream` SSE chunks. Responses contain `blocks` with `markdown_block.answer`. For deep research, the non-streaming path tracks peak answer content across all intermediate chunks since the final chunk may only contain a short summary (full report delivered mid-stream).

`api/utils.py:extract_answer()` extracts the answer from blocks, preferring the longest `ask_text*` block.

### Perplexity web API endpoints used

- `/rest/sse/perplexity_ask` — Search (SSE)
- `/rest/thread/list_ask_threads` — List threads
- `/rest/thread/{slug}` — Thread details
- `/rest/discover/feed` — Discover feed
- `/rest/spaces` — List spaces
- `/rest/collections/get_collection` — Space details
- `/rest/collections/create_collection` — Create space
- `/rest/collections/edit_collection/{uuid}` — Edit space
- `/rest/collections/delete_collection/{uuid}` — Delete space
- `/rest/collections/focused_web_config/links` — Add link to space
- `/rest/collections/list_collection_threads` — Space threads
- `/rest/collections/list_user_collections` — Flat list of user's spaces

### Follow-up queries

A search response includes a `backend_uuid`. Passing this UUID into the next query creates a follow-up in the same conversation thread.

## Key conventions

- Python 3.13+ required
- `curl-cffi` with `impersonate="chrome"` for all HTTP requests
- Cookies file (`perplexity_cookies.json`) is gitignored and auto-created on first login
- `.browser_profile/` is gitignored — persistent Playwright browser profile
- API logs responses to `logs/` directory via `utils.save_resp()`
