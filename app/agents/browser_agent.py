"""
BrowserAgent — JARVIS's hands on the web.
Can navigate websites, fill forms, extract data, click buttons, take screenshots.
Uses Playwright (sync) with headless Chromium.
"""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from app.agents.base import AgentResponse, BaseAgent

LOGGER = logging.getLogger(__name__)

# Browser screenshots output dir
BROWSER_SCREENSHOT_DIR = Path(os.getenv("BROWSER_SCREENSHOT_DIR", "data/browser_screenshots"))

try:
    from playwright.sync_api import sync_playwright, Page, Browser
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    sync_playwright = None  # type: ignore[assignment]
    _PLAYWRIGHT_AVAILABLE = False


class BrowserAgent(BaseAgent):
    """Controls web browsers — navigates, fills forms, extracts data, takes screenshots."""

    name = "BrowserAgent"
    description = (
        "Gives JARVIS hands on the web — can search Google/DuckDuckGo, navigate websites, "
        "extract data, fill forms, take webpage screenshots, and log into sites."
    )
    capabilities = [
        "Search the web (DuckDuckGo)",
        "Navigate to any URL and summarize content",
        "Extract structured data from web pages",
        "Fill and submit web forms",
        "Take screenshots of web pages",
        "Click elements on pages",
        "Log into websites",
    ]

    def __init__(self) -> None:
        super().__init__()
        BROWSER_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        if not _PLAYWRIGHT_AVAILABLE:
            LOGGER.warning(
                "BrowserAgent: playwright not installed. "
                "Install with: pip install playwright && playwright install chromium"
            )

    # ── Public agent interface ──────────────────────────────────────────────

    def handle(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Route browser queries to the correct sub-handler."""
        context = context or {}
        q = query.lower()

        url = context.get("url") or ""

        if any(kw in q for kw in ["search", "look up", "find on", "google", "duckduckgo"]):
            # Extract search term: strip "search for / look up / google"
            search_q = _strip_command_prefix(query, ["search for", "search", "look up", "google", "find on the web", "find"])
            results = self.search_web(search_q or query)
            if isinstance(results, dict) and "error" in results:
                return AgentResponse(agent=self.name, content=results["error"], status="error")
            formatted = _format_search_results(results)
            return AgentResponse(
                agent=self.name,
                content=formatted,
                data={"results": results},
                status="success",
            )

        if any(kw in q for kw in ["go to", "open", "navigate", "visit", "check the site"]) and url:
            result = self.browse(url)
        elif url and not any(kw in q for kw in ["search", "extract", "screenshot", "fill", "click", "login"]):
            result = self.browse(url)
        elif any(kw in q for kw in ["screenshot", "capture page", "snapshot of"]) and url:
            result = self.screenshot_url(url)
        elif any(kw in q for kw in ["extract", "scrape", "get data", "pull data"]) and url:
            instructions = context.get("instructions", query)
            result = self.extract_data(url, instructions)
        elif any(kw in q for kw in ["fill form", "submit form"]) and url:
            form_data = context.get("form_data", {})
            result = self.fill_form(url, form_data)
        elif any(kw in q for kw in ["login", "log in", "sign in"]) and url:
            username = context.get("username", "")
            password = context.get("password", "")
            result = self.login_to_site(url, username, password)
        elif any(kw in q for kw in ["click"]) and url:
            selector_desc = context.get("selector_description", query)
            result = self.click_element(url, selector_desc)
        elif url:
            result = self.browse(url)
        else:
            # No URL — treat as search
            results = self.search_web(query)
            if isinstance(results, dict) and "error" in results:
                return AgentResponse(agent=self.name, content=results["error"], status="error")
            formatted = _format_search_results(results)
            return AgentResponse(
                agent=self.name,
                content=formatted,
                data={"results": results},
                status="success",
            )

        if isinstance(result, dict) and "error" in result:
            return AgentResponse(agent=self.name, content=result["error"], status="error")

        content = result.get("text") or result.get("description") or result.get("message") or str(result)
        return AgentResponse(agent=self.name, content=content, data=result, status="success")

    # ── Core browser methods ────────────────────────────────────────────────

    def browse(self, url: str) -> Dict[str, Any]:
        """Navigate to URL, return page title + visible text summary."""
        if not _PLAYWRIGHT_AVAILABLE:
            return {"error": "Playwright not installed. Run: pip install playwright && playwright install chromium"}
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                )
                page = context.new_page()
                try:
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass  # Proceed with whatever loaded
                title = page.title()
                text = page.evaluate("() => document.body ? document.body.innerText : ''") or ""
                # Trim text to avoid huge payloads
                text_trimmed = text[:3000].strip()
                browser.close()
            return {
                "title": title,
                "text": text_trimmed,
                "url": url,
                "type": "browse",
            }
        except Exception as exc:
            LOGGER.exception("browse failed for %s: %s", url, exc)
            return {"error": f"Failed to browse {url}: {exc}"}

    def search_web(self, query: str) -> List[Dict[str, str]]:
        """Search DuckDuckGo and return top 5 results (no API key needed)."""
        if not _PLAYWRIGHT_AVAILABLE:
            return [{"error": "Playwright not installed. Run: pip install playwright && playwright install chromium"}]  # type: ignore[list-item]
        try:
            results: List[Dict[str, str]] = []
            encoded = quote_plus(query)
            search_url = f"https://html.duckduckgo.com/html/?q={encoded}"
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(search_url, timeout=30000, wait_until="domcontentloaded")
                # DuckDuckGo HTML interface — stable selectors
                result_elements = page.query_selector_all(".result")
                for elem in result_elements[:5]:
                    title_elem = elem.query_selector(".result__title")
                    snippet_elem = elem.query_selector(".result__snippet")
                    url_elem = elem.query_selector(".result__url")
                    title_text = title_elem.inner_text().strip() if title_elem else ""
                    snippet_text = snippet_elem.inner_text().strip() if snippet_elem else ""
                    url_text = url_elem.inner_text().strip() if url_elem else ""
                    if title_text:
                        results.append({
                            "title": title_text,
                            "snippet": snippet_text,
                            "url": url_text,
                        })
                browser.close()
            if not results:
                # Fallback: try to parse any visible text
                LOGGER.warning("DuckDuckGo returned no results for query: %s", query)
                results = [{"title": "No results found", "snippet": f"Search for: {query}", "url": ""}]
            return results
        except Exception as exc:
            LOGGER.exception("search_web failed: %s", exc)
            return [{"error": f"Web search failed: {exc}"}]  # type: ignore[list-item]

    def fill_form(self, url: str, form_data: Dict[str, str]) -> Dict[str, Any]:
        """Navigate to URL and fill a form with the provided data dict."""
        if not _PLAYWRIGHT_AVAILABLE:
            return {"error": "Playwright not installed"}
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                filled = []
                for selector, value in form_data.items():
                    try:
                        # Try name, id, placeholder selectors in sequence
                        for attr in ["name", "id", "placeholder"]:
                            locator = page.locator(f'[{attr}="{selector}"]')
                            if locator.count() > 0:
                                locator.first.fill(value)
                                filled.append(selector)
                                break
                    except Exception as e:
                        LOGGER.warning("Could not fill field %s: %s", selector, e)
                # Try to find and click submit
                submit = page.locator('button[type="submit"], input[type="submit"]')
                submitted = False
                if submit.count() > 0:
                    submit.first.click()
                    page.wait_for_load_state("networkidle", timeout=10000)
                    submitted = True
                current_url = page.url
                browser.close()
            return {
                "message": f"Form filled. Submitted: {submitted}. Now at: {current_url}",
                "filled_fields": filled,
                "submitted": submitted,
                "current_url": current_url,
                "type": "form_fill",
            }
        except Exception as exc:
            LOGGER.exception("fill_form failed: %s", exc)
            return {"error": f"Form fill failed: {exc}"}

    def extract_data(self, url: str, instructions: str) -> Dict[str, Any]:
        """Navigate to URL and extract structured data per given instructions."""
        if not _PLAYWRIGHT_AVAILABLE:
            return {"error": "Playwright not installed"}
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                try:
                    page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    pass
                # Extract all visible text + structure
                title = page.title()
                html_content = page.content()
                text = page.evaluate("() => document.body ? document.body.innerText : ''") or ""
                browser.close()
            # Return raw text for LLM to process per instructions
            return {
                "title": title,
                "url": url,
                "instructions": instructions,
                "text": text[:4000],
                "type": "data_extraction",
                "message": f"Extracted content from {url}. Instruction: {instructions}",
            }
        except Exception as exc:
            LOGGER.exception("extract_data failed: %s", exc)
            return {"error": f"Data extraction failed: {exc}"}

    def screenshot_url(self, url: str) -> Dict[str, Any]:
        """Take a screenshot of a webpage and return the saved image path."""
        if not _PLAYWRIGHT_AVAILABLE:
            return {"error": "Playwright not installed"}
        try:
            BROWSER_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
            safe_name = "".join(c if c.isalnum() else "_" for c in url)[:60]
            screenshot_path = str(BROWSER_SCREENSHOT_DIR / f"screenshot_{safe_name}.png")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                try:
                    page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    pass
                page.screenshot(path=screenshot_path, full_page=False)
                title = page.title()
                browser.close()
            return {
                "screenshot_path": screenshot_path,
                "title": title,
                "url": url,
                "message": f"Screenshot saved to {screenshot_path}",
                "type": "screenshot",
            }
        except Exception as exc:
            LOGGER.exception("screenshot_url failed: %s", exc)
            return {"error": f"Screenshot failed: {exc}"}

    def click_element(self, url: str, selector_description: str) -> Dict[str, Any]:
        """Navigate to URL and click an element described by text or selector."""
        if not _PLAYWRIGHT_AVAILABLE:
            return {"error": "Playwright not installed"}
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                # Try to find element by text content first, then as CSS selector
                clicked = False
                try:
                    page.get_by_text(selector_description, exact=False).first.click(timeout=5000)
                    clicked = True
                except Exception:
                    pass
                if not clicked:
                    try:
                        page.locator(selector_description).first.click(timeout=5000)
                        clicked = True
                    except Exception:
                        pass
                current_url = page.url if clicked else url
                title = page.title() if clicked else ""
                browser.close()
            if clicked:
                return {
                    "message": f"Clicked '{selector_description}'. Now at: {current_url}",
                    "current_url": current_url,
                    "title": title,
                    "type": "click",
                }
            else:
                return {"error": f"Could not find element: '{selector_description}'"}
        except Exception as exc:
            LOGGER.exception("click_element failed: %s", exc)
            return {"error": f"Click failed: {exc}"}

    def login_to_site(self, url: str, username: str, password: str) -> Dict[str, Any]:
        """Attempt to log into a website using common login field selectors."""
        if not _PLAYWRIGHT_AVAILABLE:
            return {"error": "Playwright not installed"}
        if not username or not password:
            return {"error": "Username and password are required for login"}
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                # Fill username/email
                for selector in [
                    'input[name="email"]', 'input[name="username"]', 'input[type="email"]',
                    'input[id*="email"]', 'input[id*="user"]', 'input[placeholder*="email" i]',
                    'input[placeholder*="username" i]',
                ]:
                    try:
                        if page.locator(selector).count() > 0:
                            page.locator(selector).first.fill(username)
                            break
                    except Exception:
                        pass
                # Fill password
                for selector in [
                    'input[type="password"]', 'input[name="password"]',
                    'input[id*="password"]', 'input[placeholder*="password" i]',
                ]:
                    try:
                        if page.locator(selector).count() > 0:
                            page.locator(selector).first.fill(password)
                            break
                    except Exception:
                        pass
                # Click submit / login button
                for selector in [
                    'button[type="submit"]', 'input[type="submit"]',
                    'button:has-text("Login")', 'button:has-text("Sign in")',
                    'button:has-text("Log in")',
                ]:
                    try:
                        if page.locator(selector).count() > 0:
                            page.locator(selector).first.click()
                            break
                    except Exception:
                        pass
                page.wait_for_load_state("networkidle", timeout=10000)
                current_url = page.url
                title = page.title()
                browser.close()
            return {
                "message": f"Login attempted. Now at: {current_url}",
                "current_url": current_url,
                "title": title,
                "type": "login",
            }
        except Exception as exc:
            LOGGER.exception("login_to_site failed: %s", exc)
            return {"error": f"Login failed: {exc}"}


# ── Internal utilities ──────────────────────────────────────────────────────

def _strip_command_prefix(query: str, prefixes: List[str]) -> str:
    """Remove common command prefixes from a query string."""
    q = query.strip()
    for prefix in sorted(prefixes, key=len, reverse=True):
        if q.lower().startswith(prefix.lower()):
            return q[len(prefix):].strip()
    return q


def _format_search_results(results: List[Dict[str, str]]) -> str:
    """Format search results into readable text."""
    if not results:
        return "No search results found."
    lines = []
    for i, r in enumerate(results, 1):
        if "error" in r:
            return r["error"]
        lines.append(f"{i}. {r.get('title', 'No title')}")
        if r.get("snippet"):
            lines.append(f"   {r['snippet']}")
        if r.get("url"):
            lines.append(f"   {r['url']}")
        lines.append("")
    return "\n".join(lines).strip()
