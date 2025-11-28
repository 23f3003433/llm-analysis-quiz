import pandas as pd
import pdfplumber
import io
import time
from bs4 import BeautifulSoup
import httpx   # async HTTP client for FastAPI


# ------------------------------------------------------------
# 1. Extract file link from HTML
# ------------------------------------------------------------
def extract_file_link(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"].lower().strip()
        if href.endswith((".csv", ".xlsx", ".xls", ".pdf")):
            return a["href"]
    return None


# ------------------------------------------------------------
# 2. Reliable file downloader (sync — OK for background work)
# ------------------------------------------------------------
def download_file(url: str, retries: int = 3, delay: int = 2) -> bytes:
    """
    For PDF/Excel that may need multiple retries.
    Uses httpx sync client instead of blocking requests.
    """
    import httpx

    for attempt in range(1, retries + 1):
        try:
            resp = httpx.get(url, timeout=20)
            resp.raise_for_status()
            return resp.content

        except Exception:
            if attempt == retries:
                raise
            time.sleep(delay)


# ------------------------------------------------------------
# 3. CSV / Excel Readers
# ------------------------------------------------------------
def read_csv(bytes_data: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(bytes_data))


def read_excel(bytes_data: bytes) -> pd.DataFrame:
    return pd.read_excel(io.BytesIO(bytes_data))


# ------------------------------------------------------------
# 4. PDF Reader — specific page
# ------------------------------------------------------------
def read_pdf_tables(bytes_data: bytes, page_number: int = 0) -> pd.DataFrame:
    with pdfplumber.open(io.BytesIO(bytes_data)) as pdf:
        if page_number >= len(pdf.pages):
            raise ValueError(
                f"PDF has only {len(pdf.pages)} pages; page {page_number} not found."
            )
        page = pdf.pages[page_number]
        tables = page.extract_tables()

    if not tables:
        raise ValueError(f"No tables found on page {page_number} of PDF.")

    df = pd.DataFrame(tables[0][1:], columns=tables[0][0])
    return df


# ------------------------------------------------------------
# 5. PDF Reader — search all pages
# ------------------------------------------------------------
def read_pdf_anywhere(bytes_data: bytes) -> pd.DataFrame:
    """
    Extract the first table found anywhere in the PDF.
    Useful fallback when page_number is unknown.
    """
    with pdfplumber.open(io.BytesIO(bytes_data)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                df = pd.DataFrame(tables[0][1:], columns=tables[0][0])
                return df

    raise ValueError("No tables found in the entire PDF.")


# ------------------------------------------------------------
# 6. Async submit answers (CRITICAL)
# ------------------------------------------------------------
async def submit_answers(submit_url: str, email: str, secret: str, answer):
    """
    ASYNC version - REQUIRED for FastAPI + Playwright.
    Uses httpx.AsyncClient (non-blocking).
    """
    payload = {
        "email": email,
        "secret": secret,
        "answer": answer,
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(submit_url, json=payload)
            resp.raise_for_status()
            return resp.json()

    except Exception as e:
        return {
            "correct": False,
            "url": "",
            "reason": f"Submit failed: {e}",
        }
