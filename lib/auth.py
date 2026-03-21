"""
Browser-based login flow for Perplexity AI.

Opens a headed Chrome browser with stealth patches so the user can log in
without being flagged as a bot. Extracts cookies after login and saves them.
"""

import json
import os
import time

# Persistent browser profile so Perplexity sees a returning user, not a fresh bot
BROWSER_DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", ".browser_profile"
)


# Cookies that indicate an authenticated Perplexity session
_SESSION_COOKIE_NAMES = {"pplx.edge-sid", "pplx.edge-vid"}


def _has_session_cookie(context) -> bool:
    """Check for Perplexity session cookies via the Playwright context API (works for httpOnly cookies)."""
    cookies = context.cookies("https://www.perplexity.ai")
    cookie_names = {c["name"] for c in cookies}
    return _SESSION_COOKIE_NAMES.issubset(cookie_names)


def login_with_browser(cookies_path: str) -> dict:
    """Launch a headed browser to perplexity.ai, wait for login, return cookies dict."""
    from playwright.sync_api import sync_playwright
    from playwright_stealth import Stealth

    print("Opening browser for Perplexity login...")
    print("Please log in. The browser will close automatically once you're signed in.")

    with Stealth().use_sync(sync_playwright()) as p:
        # Use persistent context so the profile (localStorage, IndexedDB, etc.)
        # survives across sessions — sites treat it like a real returning browser.
        context = p.chromium.launch_persistent_context(
            user_data_dir=BROWSER_DATA_DIR,
            headless=False,
            channel="chrome",  # use installed Chrome instead of bundled Chromium
            args=[
                "--disable-blink-features=AutomationControlled",
                "--force-device-scale-factor=1",
            ],
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            timezone_id="America/New_York",
        )

        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://www.perplexity.ai/", wait_until="domcontentloaded")

        # Poll for the session cookie via context API since it's httpOnly
        # and invisible to document.cookie / page.evaluate.
        deadline = time.time() + 300  # 5 minutes
        while time.time() < deadline:
            if _has_session_cookie(context):
                break
            time.sleep(1)
        else:
            context.close()
            raise TimeoutError("Login timed out after 5 minutes.")

        # Extract all cookies for perplexity.ai
        pw_cookies = context.cookies("https://www.perplexity.ai")
        cookie_dict = {c["name"]: c["value"] for c in pw_cookies}

        context.close()

    # Save to disk
    with open(cookies_path, "w", encoding="utf-8") as f:
        json.dump(cookie_dict, f, indent=2)

    print("Login successful. Cookies saved.")
    return cookie_dict
