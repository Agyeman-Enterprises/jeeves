"""
linkedin_page_creator.py — Autonomous LinkedIn company page creation.

Runs on a scheduled date trigger. Uses a saved browser session (cookies) to
navigate LinkedIn and create company pages without any human interaction.

Pages to create (from 2026-03-18 session — blocked by LinkedIn 7-day limit):
  1. MedEdConnect
  2. TaxRx
  3. EntityTaxPro

Notifies Akua via email + Pushover when done (or if it hits a problem that
needs her input). She should hear nothing unless there's a blocker.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)

COOKIES_PATH = Path("config/linkedin_session_cookies.json")
SETUP_URL = "https://www.linkedin.com/company/setup/new/"

# All three pages to create — full form data
PAGES_TO_CREATE: List[Dict[str, Any]] = [
    {
        "name": "MedEdConnect",
        "linkedin_url": "mededconnect",
        "website": "https://mededconnect.co",
        "industry": "Hospitals and Health Care",
        "size": "2–10 employees",
        "org_type": "Privately held",
        "tagline": "Graduate medical education infrastructure connecting trainees, students, and community hospitals.",
        "about": (
            "MedEdConnect is graduate medical education infrastructure built for the Pacific and "
            "underserved communities. The platform connects medical trainees and students with "
            "community hospitals offering clinical rotations — streamlining evaluation workflows, "
            "partnership agreements, and placement logistics for programs that have historically "
            "been managed on paper and email. Built by a physician who trained and practiced in "
            "the Pacific, MedEdConnect is purpose-built for the resource constraints and geographic "
            "realities of community teaching hospitals."
        ),
    },
    {
        "name": "TaxRx",
        "linkedin_url": "taxrx-ae",
        "website": "",
        "industry": "Financial Services",
        "size": "2–10 employees",
        "org_type": "Privately held",
        "tagline": "Financial clarity for physicians and solo practitioners.",
        "about": (
            "TaxRx is a financial operations platform purpose-built for physicians and solo "
            "practitioners navigating the complexity of self-employment, private practice, and "
            "multi-entity structures. Built by a physician-entrepreneur who spent years managing "
            "the intersection of clinical work and business ownership, TaxRx brings clarity to "
            "the tax, entity, and financial decisions that most financial tools weren't designed "
            "to handle."
        ),
    },
    {
        "name": "EntityTaxPro",
        "linkedin_url": "entitytaxpro",
        "website": "",
        "industry": "Financial Services",
        "size": "2–10 employees",
        "org_type": "Privately held",
        "tagline": "Multi-entity financial operations for complex business structures.",
        "about": (
            "EntityTaxPro is a financial operations platform for finance personnel and operators "
            "managing multi-entity business systems. Designed for the complexity of holding "
            "companies, subsidiaries, and intercompany transactions — EntityTaxPro handles the "
            "accounting, reporting, and tax workflows that off-the-shelf tools weren't built for. "
            "Part of the Agyeman Enterprises portfolio."
        ),
    },
]


def _set_select(page: Any, select_el: Any, value: str) -> None:
    """Set a native <select> value using React-compatible event dispatch."""
    page.evaluate(
        """([el, val]) => {
            const setter = Object.getOwnPropertyDescriptor(
                window.HTMLSelectElement.prototype, 'value'
            ).set;
            setter.call(el, val);
            el.dispatchEvent(new Event('change', { bubbles: true }));
        }""",
        [select_el, value],
    )


def _set_input(page: Any, input_el: Any, value: str) -> None:
    """Set a React-controlled input value."""
    page.evaluate(
        """([el, val]) => {
            const setter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            setter.call(el, val);
            el.dispatchEvent(new Event('input', { bubbles: true }));
        }""",
        [input_el, value],
    )


def _set_contenteditable(page: Any, el: Any, value: str) -> None:
    """Replace content in a contenteditable element."""
    el.click()
    page.evaluate(
        """([el, val]) => {
            el.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('insertText', false, val);
        }""",
        [el, value],
    )


def _fill_industry_typeahead(page: Any, industry: str) -> bool:
    """Type into the industry typeahead and select the matching option."""
    try:
        industry_input = page.locator("input[placeholder*='ndustr'], input[id*='ndustr']").first
        if not industry_input.is_visible(timeout=3000):
            # Try by aria-label
            industry_input = page.get_by_label("Industry").first
        industry_input.click()
        industry_input.fill(industry[:6])
        time.sleep(1.2)
        # Click first matching option in the dropdown
        option = page.locator(f"[role='option']:has-text('{industry}')").first
        option.wait_for(state="visible", timeout=5000)
        option.click()
        return True
    except Exception as exc:
        LOGGER.warning("Industry typeahead failed for '%s': %s", industry, exc)
        return False


def create_page(page: Any, page_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Navigate to the LinkedIn company creation form and submit one page.
    Returns dict with success bool, url of created page (if available), and any error.
    """
    LOGGER.info("[LinkedIn] Creating page: %s", page_data["name"])

    page.goto(SETUP_URL, wait_until="domcontentloaded", timeout=30000)
    time.sleep(2)

    try:
        # ── Company name ──────────────────────────────────────────────────
        name_input = page.locator("input[id*='name'], input[placeholder*='name' i]").first
        name_input.wait_for(state="visible", timeout=10000)
        _set_input(page, name_input.element_handle(), page_data["name"])
        time.sleep(0.5)

        # ── LinkedIn URL ──────────────────────────────────────────────────
        url_input = page.locator("input[id*='url'], input[placeholder*='url' i]").first
        if url_input.is_visible(timeout=2000):
            url_input.clear()
            _set_input(page, url_input.element_handle(), page_data["linkedin_url"])
            time.sleep(0.5)

        # ── Website ───────────────────────────────────────────────────────
        if page_data.get("website"):
            website_input = page.locator("input[id*='website'], input[placeholder*='website' i]").first
            if website_input.is_visible(timeout=2000):
                _set_input(page, website_input.element_handle(), page_data["website"])
                time.sleep(0.3)

        # ── Industry typeahead ────────────────────────────────────────────
        _fill_industry_typeahead(page, page_data["industry"])
        time.sleep(0.5)

        # ── Organization size <select> ────────────────────────────────────
        selects = page.locator("select").all()
        if len(selects) >= 1:
            _set_select(page, selects[0].element_handle(), page_data["size"])
            time.sleep(0.3)

        # ── Organization type <select> ────────────────────────────────────
        if len(selects) >= 2:
            _set_select(page, selects[1].element_handle(), page_data["org_type"])
            time.sleep(0.3)

        # ── Tagline ───────────────────────────────────────────────────────
        tagline_el = page.locator("textarea[id*='tagline'], input[id*='tagline']").first
        if not tagline_el.is_visible(timeout=2000):
            tagline_el = page.locator("textarea").first
        if tagline_el.is_visible(timeout=2000):
            _set_input(page, tagline_el.element_handle(), page_data["tagline"])
            time.sleep(0.3)

        # ── T&C checkbox ──────────────────────────────────────────────────
        checkbox = page.locator("input[type='checkbox']").first
        if checkbox.is_visible(timeout=2000) and not checkbox.is_checked():
            checkbox.check()
            time.sleep(0.3)

        # ── Submit ────────────────────────────────────────────────────────
        create_btn = page.locator("button:has-text('Create page')").first
        create_btn.wait_for(state="visible", timeout=5000)
        create_btn.click()
        time.sleep(3)

        # ── Detect success: URL should change away from /setup/new/ ───────
        current_url = page.url
        if "setup/new" not in current_url:
            LOGGER.info("[LinkedIn] Page '%s' created — URL: %s", page_data["name"], current_url)
            return {"success": True, "url": current_url, "name": page_data["name"]}

        # Check for error messages on page
        error_els = page.locator("[class*='error'], [class*='alert']").all()
        error_text = " | ".join(e.text_content() for e in error_els if e.text_content())
        return {
            "success": False,
            "name": page_data["name"],
            "error": error_text or "Still on setup/new after clicking Create",
        }

    except Exception as exc:
        LOGGER.error("[LinkedIn] Exception creating page '%s': %s", page_data["name"], exc)
        return {"success": False, "name": page_data["name"], "error": str(exc)}


def run_linkedin_page_creation() -> Dict[str, Any]:
    """
    Main entry point called by the scheduler.
    Launches headless Chromium, injects saved cookies, creates all 3 pages,
    then adds About sections to created pages.
    Returns summary dict with results for notification.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {
            "success": False,
            "error": "Playwright not installed. Run: pip install playwright && playwright install chromium",
        }

    if not COOKIES_PATH.exists():
        return {
            "success": False,
            "error": f"LinkedIn session cookies not found at {COOKIES_PATH}. Re-authenticate LinkedIn.",
        }

    with open(COOKIES_PATH) as f:
        cookies = json.load(f)

    results = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        )
        # Inject saved session cookies
        context.add_cookies(cookies)
        page = context.new_page()

        # Verify we're logged in
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=20000)
        time.sleep(2)
        if "login" in page.url.lower() or "authwall" in page.url.lower():
            browser.close()
            return {
                "success": False,
                "error": (
                    "LinkedIn session expired. Cookies need to be refreshed. "
                    "Open JARVIS browser session, log into LinkedIn manually, then re-run "
                    "linkedin_page_creator.refresh_cookies()."
                ),
            }

        LOGGER.info("[LinkedIn] Session valid. Starting page creation.")

        for page_data in PAGES_TO_CREATE:
            result = create_page(page, page_data)
            results.append(result)
            time.sleep(2)  # Polite pause between submissions

            # If successful, add About section
            if result.get("success") and result.get("url"):
                _add_about_section(page, result["url"], page_data.get("about", ""))

        browser.close()

    created = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]

    return {
        "success": len(failed) == 0,
        "created": created,
        "failed": failed,
        "summary": (
            f"LinkedIn pages: {len(created)}/3 created successfully."
            + (f" Failures: {', '.join(f['name'] for f in failed)}" if failed else "")
        ),
    }


def _add_about_section(page: Any, company_url: str, about_text: str) -> None:
    """Navigate to the company About edit page and add the About section."""
    if not about_text:
        return
    try:
        # Extract company handle from URL to build the edit URL
        # URL pattern: /company/mededconnect/ or /company/mededconnect/admin/
        edit_url = company_url.rstrip("/") + "/edit/about/"
        if "/company/" not in edit_url:
            LOGGER.warning("[LinkedIn] Cannot build About edit URL from: %s", company_url)
            return

        page.goto(edit_url, wait_until="domcontentloaded", timeout=20000)
        time.sleep(2)

        # Find the About textarea or contenteditable
        about_el = page.locator("textarea[id*='summary'], textarea[name*='summary']").first
        if not about_el.is_visible(timeout=3000):
            about_el = page.locator("[contenteditable='true']").first

        if about_el.is_visible(timeout=3000):
            about_el.click()
            page.evaluate(
                """([el, val]) => {
                    el.focus();
                    document.execCommand('selectAll', false, null);
                    document.execCommand('insertText', false, val);
                }""",
                [about_el.element_handle(), about_text],
            )
            time.sleep(0.5)
            save_btn = page.locator("button:has-text('Save')").first
            if save_btn.is_visible(timeout=3000):
                save_btn.click()
                time.sleep(2)
                LOGGER.info("[LinkedIn] About section added for %s", company_url)
    except Exception as exc:
        LOGGER.warning("[LinkedIn] Could not add About section for %s: %s", company_url, exc)
