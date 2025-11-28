import aiohttp
from playwright.async_api import async_playwright


# ------------------------------------------------------------
# JS-rendered HTML fetcher (Playwright)
# ------------------------------------------------------------
async def fetch_rendered_page(url: str) -> dict:
    """
    Fetch dynamically rendered HTML using Playwright.
    Used for quizzes requiring JS (PDF, API, visualization, HTML tables).
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Wait for the page to fully load JS content
            await page.goto(url, timeout=60000, wait_until="networkidle")

            html = await page.content()
            text = await page.inner_text("body")

            await browser.close()

            return {"html": html, "text": text}

    except Exception as e:
        print("Playwright Error:", type(e), e)
        return {"html": "", "text": ""}


# ------------------------------------------------------------
# FAST plain HTML fetcher (non-JS pages, audio quiz)
# ------------------------------------------------------------
async def fetch_html(url: str) -> str | None:
    """
    Fetch plain HTML using aiohttp.
    Use this ONLY for simple pages (like audio quiz) where JS isn't required.
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.text()
        except Exception as e:
            print("Error fetching HTML:", e)
    return None


# ------------------------------------------------------------
# Async file downloader (CSV, PDF, Excel)
# ------------------------------------------------------------
async def fetch_file(url: str) -> bytes | None:
    """
    Download a file and return raw bytes.
    This is async and safe for FastAPI.
    """
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.read()
        except Exception as e:
            print("Error downloading file:", e)
    return None
