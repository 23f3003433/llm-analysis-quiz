import re
import pandas as pd
from io import StringIO
from pydantic import BaseModel

from .fetch import fetch_html, fetch_file
from .parser import extract_answer_from_audio, extract_submit_url
from .handlers import submit_answers
from urllib.parse import urlparse


class QuizRequest(BaseModel):
    email: str
    secret: str
    url: str


# ------------------------------------------------------------
# Build submit URL when HTML does not contain it
# ------------------------------------------------------------
def derive_submit_url_from_request(url: str) -> str:
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    return origin + "/submit"


# ------------------------------------------------------------
# Solve chain for audio question
# ------------------------------------------------------------
async def solve_quiz_chain(chain_req, url: str):
    """
    Solver steps:
        1. Fetch HTML (raw)
        2. Extract CSV link
        3. Fix relative CSV URL
        4. Download CSV
        5. Compute answer
        6. Extract SUBMIT URL (via parser or fallback)
        7. Submit answer
    """

    # 1. Fetch HTML
    html = await fetch_html(url)
    if html is None:
        return {
            "correct": False,
            "url": "",
            "reason": "Failed to fetch HTML"
        }

    # 2. Extract CSV link
    m = re.search(r'href="([^"]+\.csv)"', html)
    if not m:
        return {
            "correct": False,
            "url": "",
            "reason": "CSV link not found"
        }

    csv_url = m.group(1).strip()

    # 3. Fix relative URL
    base = url.split("/demo-audio")[0]

    if csv_url.startswith("http"):
        pass
    elif csv_url.startswith("/"):
        csv_url = base + csv_url
    else:
        csv_url = base + "/" + csv_url

    # 4. Download CSV
    csv_bytes = await fetch_file(csv_url)
    if csv_bytes is None:
        return {
            "correct": False,
            "url": "",
            "reason": f"Failed to download CSV file: {csv_url}"
        }

    # 5. Compute answer
    try:
        answer = extract_answer_from_audio(html, csv_bytes, chain_req.email)
    except Exception as e:
        return {
            "correct": False,
            "url": "",
            "reason": str(e)
        }

    # 6. Extract SUBMIT URL
    submit_url = extract_submit_url(html)

    # Fallback if HTML did not contain submit URL
    if not submit_url or not submit_url.startswith("http"):
        submit_url = derive_submit_url_from_request(url)

    # 7. Submit the answer
    submit_result = await submit_answers(
        submit_url=submit_url,
        email=chain_req.email,
        secret=chain_req.secret,
        answer=answer,
    )

    # 8. Return the final result
    return {
        "correct": submit_result.get("correct", False),
        "url": submit_result.get("url", ""),
        "reason": submit_result.get("reason", ""),
        "answer_used": answer,
    }
