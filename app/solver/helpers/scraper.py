# app/solver/helpers/scraper.py

from typing import Optional

from ..fetch import fetch_html


async def scrape_page(url: str) -> Optional[str]:
    """
    Generic page scraper.

    Delegates to fetch_html which should handle:
    - normal HTTP GET
    - JS-rendered pages via headless browser (Playwright, etc.) if you implemented it there.
    """
    html = await fetch_html(url)
    return html
