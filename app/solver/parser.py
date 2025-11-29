# app/solver/parser.py

from bs4 import BeautifulSoup
from urllib.parse import urljoin


def extract_submit_url(html: str) -> str | None:
    """
    Extracts submit URL from the quiz HTML.
    Often appears inside the page as:
      Post your answer to <span class="origin"></span>/submit
    or as an <a href=...> link.
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1. Look for explicit URLs inside <a> tags
    for a in soup.find_all("a"):
        href = a.get("href", "")
        if "submit" in href:
            return href

    # 2. Look for "submit" text inside script or embedded content
    text = soup.get_text(" ", strip=True)
    possible = [word for word in text.split() if "submit" in word.lower()]
    if possible:
        return possible[0]

    return None


def extract_input_links(html: str, base_url: str) -> list:
    """
    Extract all downloadable file URLs:
    - CSV
    - PDF
    - JSON
    - Images
    - Anything with <a href="...">

    The chain/LLM will filter them out and decide which to load.
    """
    soup = BeautifulSoup(html, "html.parser")

    links = []
    for a in soup.find_all("a"):
        href = a.get("href")
        if not href:
            continue

        full_url = urljoin(base_url, href)
        links.append(full_url)

    return links


def parse_question_text(html: str) -> str:
    """
    Extract visible question text from HTML.

    Used only as context for the LLM.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Priority: <p>, <div>, <h1>.. <h6>
    parts = []

    for tag in soup.find_all(["p", "div", "span", "h1","h2","h3","h4","h5","h6"]):
        txt = tag.get_text(" ", strip=True)
        if txt:
            parts.append(txt)

    # Return a joined block of readable text
    return "\n".join(parts)
