"""
CLI for Perplexity AI wrapper.

Usage:
    uv run cli.py search "your query" [--mode auto|pro|reasoning|deep research] [--model MODEL] [--sources web,scholar] [--language en-US]
    uv run cli.py threads [--limit 20] [--offset 0] [--search TERM]
    uv run cli.py thread SLUG
    uv run cli.py discover [--next-token TOKEN]
    uv run cli.py spaces
    uv run cli.py space SLUG
    uv run cli.py space:create TITLE [--description DESC] [--instructions INST] [--access 0|1|2]
    uv run cli.py space:edit UUID [--title T] [--description D] [--instructions I] [--access A]
    uv run cli.py space:delete UUID
    uv run cli.py space:add-link UUID URL
    uv run cli.py space:threads SLUG [--limit 20]
    uv run cli.py login
"""

import argparse
import json
import os
import sys

COOKIES_PATH = os.environ.get(
    "PERPLEXITY_COOKIES_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "perplexity_cookies.json"),
)


def get_client():
    from lib.perplexity import Client

    try:
        with open(COOKIES_PATH) as f:
            cookies = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cookies = {}
    return Client(cookies, cookies_path=COOKIES_PATH)


def cmd_login(_args):
    from lib.auth import login_with_browser

    login_with_browser(COOKIES_PATH)


def cmd_search(args):
    from api.utils import extract_answer

    client = get_client()
    sources_list = [s.strip() for s in args.sources.split(",")]
    follow_up = None
    if args.follow_up:
        follow_up = {"backend_uuid": args.follow_up, "attachments": []}

    resp = client.search(
        query=args.query,
        mode=args.mode,
        model=args.model,
        sources=sources_list,
        language=args.language,
        follow_up=follow_up,
        incognito=args.incognito,
    )

    if resp is None:
        print("No response received.")
        return

    result = extract_answer(resp, "cli_search")
    if result.get("report_title"):
        print(f"# {result['report_title']}\n")
    if result.get("answer"):
        print(result["answer"])
    sources = result.get("sources")
    if sources:
        print("\n## Sources")
        for s in sources:
            print(f"[{s['index']}] {s['name']}: {s['url']}")
    if result.get("backend_uuid"):
        print(f"\n[backend_uuid: {result['backend_uuid']}]")


def cmd_threads(args):
    client = get_client()
    threads = client.get_threads(limit=args.limit, offset=args.offset, search_term=args.search)
    for t in threads:
        title = t.get("title", t.get("query_str", "?"))
        slug = t.get("slug", "")
        status = t.get("status", "")
        print(f"  {title[:70]:<72s} {status:<12s} {slug}")


def cmd_thread(args):
    client = get_client()
    resp = client.get_thread_details_by_slug(args.slug)
    print(json.dumps(resp, indent=2))


def cmd_discover(args):
    client = get_client()
    resp = client.get_discover_feed(next_token=args.next_token)
    items = resp.get("items", [])
    for item in items:
        title = item.get("title", "?")
        url = item.get("url", "")
        print(f"  {title[:80]}")
        if url:
            print(f"    {url}")
    next_token = resp.get("next_token")
    if next_token:
        print(f"\n  --next-token {next_token}")


def cmd_spaces(_args):
    client = get_client()
    resp = client.list_spaces()
    for category, spaces in resp.items():
        if not spaces:
            continue
        print(f"\n{category}:")
        for s in spaces:
            print(f"  {s.get('title', '?'):<40s} uuid={s['uuid']}  slug={s.get('slug', '')}")


def cmd_space(args):
    client = get_client()
    resp = client.get_space(args.slug)
    print(f"Title:        {resp.get('title')}")
    print(f"Description:  {resp.get('description') or '(none)'}")
    print(f"Instructions: {resp.get('instructions') or '(none)'}")
    print(f"UUID:         {resp.get('uuid')}")
    print(f"Access:       {resp.get('access')}")
    links = resp.get("focused_web_config", {}).get("link_configs", [])
    if links:
        print(f"Links:")
        for link in links:
            print(f"  - {link.get('link')}")


def cmd_space_create(args):
    client = get_client()
    resp = client.create_space(
        title=args.title,
        description=args.description,
        instructions=args.instructions,
        access=args.access,
    )
    print(f"Created: {resp.get('title')}  uuid={resp.get('uuid')}  slug={resp.get('slug')}")


def cmd_space_edit(args):
    client = get_client()
    resp = client.edit_space(
        collection_uuid=args.uuid,
        title=args.title,
        description=args.description,
        instructions=args.instructions,
        access=args.access,
    )
    print(f"Updated: {resp.get('title', 'ok')}")


def cmd_space_delete(args):
    client = get_client()
    client.delete_space(args.uuid)
    print(f"Deleted: {args.uuid}")


def cmd_space_add_link(args):
    client = get_client()
    client.add_space_link(args.uuid, args.url)
    print(f"Added link: {args.url}")


def cmd_space_threads(args):
    client = get_client()
    threads = client.list_space_threads(args.slug, limit=args.limit, offset=args.offset)
    if not threads:
        print("  (no threads)")
        return
    for t in threads:
        print(f"  {t.get('title', '?')[:70]}")


def main():
    parser = argparse.ArgumentParser(description="Perplexity AI CLI")
    sub = parser.add_subparsers(dest="command")

    # login
    sub.add_parser("login", help="Log in via browser")

    # search
    p = sub.add_parser("search", help="Search Perplexity AI")
    p.add_argument("query", help="Search query")
    p.add_argument("--mode", default="auto", choices=["auto", "pro", "reasoning", "deep research"])
    p.add_argument("--model", default=None)
    p.add_argument("--sources", default="web", help="Comma-separated: web,scholar,social")
    p.add_argument("--language", default="en-US")
    p.add_argument("--follow-up", default=None, help="backend_uuid for follow-up")
    p.add_argument("--incognito", action="store_true")

    # threads
    p = sub.add_parser("threads", help="List threads")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--search", default="")

    # thread
    p = sub.add_parser("thread", help="Get thread details")
    p.add_argument("slug")

    # discover
    p = sub.add_parser("discover", help="Discover feed")
    p.add_argument("--next-token", default=None)

    # spaces
    sub.add_parser("spaces", help="List spaces")

    # space
    p = sub.add_parser("space", help="Get space details")
    p.add_argument("slug")

    # space:create
    p = sub.add_parser("space:create", help="Create a space")
    p.add_argument("title")
    p.add_argument("--description", default="")
    p.add_argument("--instructions", default="")
    p.add_argument("--access", type=int, default=0, help="0=private, 1=link, 2=shared")

    # space:edit
    p = sub.add_parser("space:edit", help="Edit a space")
    p.add_argument("uuid")
    p.add_argument("--title", default=None)
    p.add_argument("--description", default=None)
    p.add_argument("--instructions", default=None)
    p.add_argument("--access", type=int, default=None)

    # space:delete
    p = sub.add_parser("space:delete", help="Delete a space")
    p.add_argument("uuid")

    # space:add-link
    p = sub.add_parser("space:add-link", help="Add link to space")
    p.add_argument("uuid")
    p.add_argument("url")

    # space:threads
    p = sub.add_parser("space:threads", help="List space threads")
    p.add_argument("slug")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--offset", type=int, default=0)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "login": cmd_login,
        "search": cmd_search,
        "threads": cmd_threads,
        "thread": cmd_thread,
        "discover": cmd_discover,
        "spaces": cmd_spaces,
        "space": cmd_space,
        "space:create": cmd_space_create,
        "space:edit": cmd_space_edit,
        "space:delete": cmd_space_delete,
        "space:add-link": cmd_space_add_link,
        "space:threads": cmd_space_threads,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
