# 🔍 Perplexity Web Wrapper API & MCP

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-stdio-purple.svg)](https://modelcontextprotocol.io)
[![uv](https://img.shields.io/badge/uv-package-orange.svg)](https://github.com/astral-sh/uv)

> Unofficial Perplexity AI client that works **without the official API**.
> Fork of [saiteja-madha/perplexity-web-wrapper](https://github.com/saiteja-madha/perplexity-web-wrapper), updated for the current Perplexity website.

> **Related**: [notebooklm-mcp-cli](https://github.com/jacob-bd/notebooklm-mcp-cli) — Google NotebookLM as an MCP server

> [!WARNING]
> **This project may not comply with Perplexity AI's Terms of Service.** It works by automating a browser session against the Perplexity website — not through any official API. Use at your own risk. Your account may be rate-limited or banned. The author is not responsible for any consequences.

![demo](docs/demo.gif)

### ✨ What's New

| Feature | Description |
|---------|-------------|
| 🤖 **MCP Server** | 11 tools for Claude Code and other AI assistants (stdio) |
| 💻 **CLI** | Full-featured command-line interface |
| 📰 **Discover Feed** | Browse trending topics and articles |
| 📂 **Spaces** | Full CRUD — create, edit, delete, add links, list threads |
| 📝 **Deep Research** | Captures the full report, not just the summary |
| 🔐 **Auto-login** | Playwright + stealth browser login, no manual cookie export |
| 🍪 **Cookie Persistence** | Session stays fresh across restarts automatically |

---

## 🚀 Setup

### CLI

Quick install (global, no clone needed):

```sh
uv tool install git+https://github.com/eryawww/perplexity-web-wrapper-mcp.git
playwright install chromium
```

To update or uninstall:

```sh
uv tool install git+https://github.com/eryawww/perplexity-web-wrapper-mcp.git --force  # update
uv tool uninstall perplexity-web-wrapper                                                # remove
```

<details>
<summary>📦 Development install (if you want to modify the code)</summary>

```sh
git clone https://github.com/eryawww/perplexity-web-wrapper-mcp.git
cd perplexity-web-wrapper-mcp
uv sync
uv run playwright install chromium
# use `uv run perplexity` instead of `perplexity`
```

</details>

### MCP & Claude Code

**Step 1** — Install the package:

```sh
uv tool install git+https://github.com/eryawww/perplexity-web-wrapper-mcp.git
playwright install chromium
```

**Step 2** — Register with Claude Code:

```sh
claude mcp add perplexity -- perplexity-mcp
```

**Step 3** — Start Claude Code and try:

> *"Search Perplexity for the latest AI news"*

On first use, a browser window opens for you to log in. After that, it's fully automatic.

To remove:

```sh
claude mcp remove perplexity
uv tool uninstall perplexity-web-wrapper
```

<details>
<summary>⚙️ Manual MCP config (for other clients)</summary>

```json
{
  "mcpServers": {
    "perplexity": {
      "command": "perplexity-mcp"
    }
  }
}
```

</details>

---

## 📖 Usage

### CLI

```sh
# 🔐 Login (or auto-triggered on first use)
perplexity login

# 🔎 Search
perplexity search "what is quantum computing"
perplexity search "compare React vs Vue" --mode pro
perplexity search "explain transformers" --mode "deep research"
perplexity search "follow up question" --follow-up BACKEND_UUID

# 🧵 Threads
perplexity threads
perplexity threads --search "python" --limit 5
perplexity thread SLUG

# 📰 Discover
perplexity discover

# 📂 Spaces
perplexity spaces
perplexity space SLUG
perplexity space:create "My Research" --instructions "Focus on academic sources"
perplexity space:edit UUID --title "New Title" --instructions "Be concise"
perplexity space:add-link UUID "docs.python.org"
perplexity space:threads SLUG
perplexity space:delete UUID
```

### Claude Code Prompts

Once the MCP server is registered, you can ask Claude directly:

| Prompt | What happens |
|--------|-------------|
| *"Search Perplexity for Redis vs Memcached benchmarks"* | Calls `search` with mode auto |
| *"Do a deep research on Python async HTTP libraries"* | Calls `search` with mode deep research |
| *"Show me trending topics on Perplexity"* | Calls `discover_feed` |
| *"List my Perplexity spaces"* | Calls `list_spaces` |
| *"Create a space called ML Papers with instructions to focus on arxiv"* | Calls `create_space` |
| *"Add docs.python.org as a source to space UUID"* | Calls `add_space_link` |

---

## 🛠️ APIs and Tools

### Available API

The Python library can be used directly:

```python
from lib.perplexity import Client

client = Client(cookies={}, cookies_path="perplexity_cookies.json")
```

| Method | Description | Example |
|--------|-------------|---------|
| `search()` | Query with modes, models, sources, follow-ups | `client.search("query", mode="pro", model="claude 3.7 sonnet")` |
| `get_threads()` | List conversation threads | `client.get_threads(limit=10, search_term="python")` |
| `get_thread_details_by_slug()` | Get full thread history | `client.get_thread_details_by_slug("thread-slug-abc")` |
| `get_discover_feed()` | Trending topics and articles | `client.get_discover_feed()` |
| `list_spaces()` | All spaces grouped by category | `client.list_spaces()` |
| `get_space()` | Space details, instructions, links | `client.get_space("my-space-slug")` |
| `create_space()` | Create a new space | `client.create_space("Title", instructions="Be concise")` |
| `edit_space()` | Update space settings | `client.edit_space(uuid, instructions="New instructions")` |
| `delete_space()` | Delete a space | `client.delete_space(uuid)` |
| `add_space_link()` | Add focused web source | `client.add_space_link(uuid, "docs.python.org")` |
| `list_space_threads()` | Threads within a space | `client.list_space_threads("my-space-slug")` |

#### 🔎 Search Modes & Models

| Mode | Available Models | Description |
|------|-----------------|-------------|
| `auto` | *(default)* | Quick answers |
| `pro` | `sonar` · `gpt-4.5` · `gpt-4o` · `claude 3.7 sonnet` · `gemini 2.0 flash` · `grok-2` | Enhanced search with model selection |
| `reasoning` | `r1` · `o3-mini` · `claude 3.7 sonnet` | Step-by-step reasoning |
| `deep research` | *(default)* | Multi-step research with full report |

### Available Tools

MCP tools exposed via `perplexity-mcp` (stdio transport):

| Tool | Arguments | Description |
|------|-----------|-------------|
| `search` | `query`, `mode?`, `model?`, `sources?`, `language?`, `backend_uuid?`, `incognito?` | Search Perplexity AI |
| `get_threads` | `limit?`, `offset?`, `search_term?` | List conversation threads |
| `get_thread` | `slug` | Get thread details |
| `discover_feed` | `next_token?` | Browse trending topics |
| `list_spaces` | — | List all Spaces |
| `get_space` | `collection_slug` | Get Space details |
| `create_space` | `title`, `description?`, `instructions?`, `emoji?`, `access?` | Create a Space |
| `edit_space` | `collection_uuid`, `title?`, `description?`, `instructions?`, `emoji?`, `access?` | Update Space settings |
| `delete_space` | `collection_uuid` | Delete a Space |
| `add_space_link` | `collection_uuid`, `link` | Add focused web link |
| `list_space_threads` | `collection_slug`, `limit?`, `offset?`, `filter_by_user?` | List threads in a Space |

---

## 🙏 Acknowledgements

Built on top of [**saiteja-madha/perplexity-web-wrapper**](https://github.com/saiteja-madha/perplexity-web-wrapper) which provided the original Perplexity web client and FastAPI server.

## 📝 Notes

- This is an **unofficial** project, not affiliated with Perplexity AI.
- Requires **Python 3.13+**.
- Uses `curl-cffi` with Chrome impersonation to bypass bot detection.
- An optional **FastAPI server** is also included — run with `uvicorn api.main:app --reload` and see `/docs` for Swagger UI.

## 📄 License

MIT
