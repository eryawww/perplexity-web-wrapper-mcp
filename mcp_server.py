"""
MCP server for Perplexity AI (stdio transport).

Usage:
    uv run mcp_server.py
"""

import json
import os

from mcp.server.fastmcp import FastMCP

from lib.perplexity import Client

mcp = FastMCP("Perplexity AI")

COOKIES_PATH = os.environ.get(
    "PERPLEXITY_COOKIES_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "perplexity_cookies.json"),
)

_client = None


def get_client() -> Client:
    global _client
    if _client is None:
        try:
            with open(COOKIES_PATH) as f:
                cookies = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cookies = {}
        _client = Client(cookies, cookies_path=COOKIES_PATH)
    return _client


@mcp.tool()
def search(
    query: str,
    mode: str = "auto",
    model: str | None = None,
    sources: str = "web",
    language: str = "en-US",
    backend_uuid: str | None = None,
    incognito: bool = False,
) -> str:
    """Search Perplexity AI and return the answer.

    Args:
        query: The search query.
        mode: Search mode - one of 'auto', 'pro', 'reasoning', 'deep research'.
        model: Model to use (mode-dependent). Pro: sonar, gpt-4.5, gpt-4o, claude 3.7 sonnet, gemini 2.0 flash, grok-2. Reasoning: r1, o3-mini, claude 3.7 sonnet. None for default.
        sources: Comma-separated sources: web, scholar, social.
        language: Language code (e.g. en-US).
        backend_uuid: UUID from a previous response to continue a conversation (follow-up query).
        incognito: Enable incognito mode.
    """
    client = get_client()
    sources_list = [s.strip() for s in sources.split(",")]

    follow_up = None
    if backend_uuid:
        follow_up = {"backend_uuid": backend_uuid, "attachments": []}

    resp = client.search(
        query=query,
        mode=mode,
        model=model,
        sources=sources_list,
        language=language,
        follow_up=follow_up,
        incognito=incognito,
    )

    if resp is None:
        return "No response received from Perplexity."

    # Extract answer from response blocks
    from api.utils import extract_answer

    result = extract_answer(resp, "mcp_search")
    answer = result.get("answer")
    result_backend_uuid = result.get("backend_uuid")

    parts = []
    if answer:
        parts.append(answer)
    sources = result.get("sources")
    if sources:
        parts.append("\n\n## Sources")
        for s in sources:
            parts.append(f"\n[{s['index']}] {s['name']}: {s['url']}")
    if result_backend_uuid:
        parts.append(f"\n\n[backend_uuid: {result_backend_uuid}]")

    return "".join(parts) if parts else json.dumps(resp, indent=2)


@mcp.tool()
def get_threads(limit: int = 20, offset: int = 0, search_term: str = "") -> str:
    """List conversation threads from Perplexity AI.

    Args:
        limit: Number of threads to fetch.
        offset: Pagination offset.
        search_term: Filter threads by search term.
    """
    client = get_client()
    resp = client.get_threads(limit=limit, offset=offset, search_term=search_term)
    return json.dumps(resp, indent=2)


@mcp.tool()
def get_thread(slug: str) -> str:
    """Get full details of a Perplexity AI conversation thread.

    Args:
        slug: The thread slug identifier.
    """
    client = get_client()
    resp = client.get_thread_details_by_slug(slug)
    return json.dumps(resp, indent=2)


# ── Discover ──────────────────────────────────────────────────────


@mcp.tool()
def discover_feed(next_token: str | None = None) -> str:
    """Get the Perplexity Discover feed (trending topics and articles).

    Args:
        next_token: Pagination token from a previous response for the next page.
    """
    client = get_client()
    resp = client.get_discover_feed(next_token=next_token)
    # Return a summary: items with key fields only
    items = resp.get("items", [])
    summary = {
        "next_token": resp.get("next_token"),
        "items": [
            {
                "title": item.get("title"),
                "summary": item.get("summary"),
                "url": item.get("url"),
                "slug": item.get("slug"),
                "sources": item.get("web_results_preview", {}).get("first_urls", [])[:3],
                "updated": item.get("updated_datetime"),
            }
            for item in items
        ],
    }
    return json.dumps(summary, indent=2)


# ── Spaces ────────────────────────────────────────────────────────


@mcp.tool()
def list_spaces() -> str:
    """List all Perplexity Spaces grouped by category (private, shared, invited, saved, organization)."""
    client = get_client()
    resp = client.list_spaces()
    return json.dumps(resp, indent=2)


@mcp.tool()
def get_space(collection_slug: str) -> str:
    """Get details of a Perplexity Space including its settings, instructions, and links.

    Args:
        collection_slug: The space slug identifier.
    """
    client = get_client()
    resp = client.get_space(collection_slug)
    return json.dumps(resp, indent=2)


@mcp.tool()
def create_space(
    title: str,
    description: str = "",
    instructions: str = "",
    emoji: str = "",
    access: int = 0,
) -> str:
    """Create a new Perplexity Space.

    Args:
        title: Space title.
        description: Space description.
        instructions: AI instructions for queries within this space.
        emoji: Emoji icon for the space.
        access: 0 = private, 1 = anyone with link, 2 = shared.
    """
    client = get_client()
    resp = client.create_space(
        title=title,
        description=description,
        instructions=instructions,
        emoji=emoji,
        access=access,
    )
    return json.dumps(resp, indent=2)


@mcp.tool()
def edit_space(
    collection_uuid: str,
    title: str | None = None,
    description: str | None = None,
    instructions: str | None = None,
    emoji: str | None = None,
    access: int | None = None,
) -> str:
    """Update a Perplexity Space's settings.

    Args:
        collection_uuid: UUID of the space to edit.
        title: New title (leave empty to keep current).
        description: New description.
        instructions: New AI instructions.
        emoji: New emoji.
        access: New access level (0=private, 1=link, 2=shared).
    """
    client = get_client()
    resp = client.edit_space(
        collection_uuid=collection_uuid,
        title=title,
        description=description,
        instructions=instructions,
        emoji=emoji,
        access=access,
    )
    return json.dumps(resp, indent=2)


@mcp.tool()
def delete_space(collection_uuid: str) -> str:
    """Delete a Perplexity Space.

    Args:
        collection_uuid: UUID of the space to delete.
    """
    client = get_client()
    resp = client.delete_space(collection_uuid)
    return json.dumps(resp, indent=2)


@mcp.tool()
def add_space_link(collection_uuid: str, link: str) -> str:
    """Add a focused web link to a Perplexity Space.

    Args:
        collection_uuid: UUID of the space.
        link: URL to add as a focused source (e.g. "example.com").
    """
    client = get_client()
    resp = client.add_space_link(collection_uuid, link)
    return json.dumps(resp, indent=2)


@mcp.tool()
def list_space_threads(
    collection_slug: str,
    limit: int = 20,
    offset: int = 0,
    filter_by_user: bool = False,
) -> str:
    """List threads in a Perplexity Space.

    Args:
        collection_slug: The space slug identifier.
        limit: Number of threads to fetch.
        offset: Pagination offset.
        filter_by_user: If true, only show your own threads.
    """
    client = get_client()
    resp = client.list_space_threads(
        collection_slug=collection_slug,
        limit=limit,
        offset=offset,
        filter_by_user=filter_by_user,
    )
    return json.dumps(resp, indent=2)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
