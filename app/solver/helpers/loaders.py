# app/solver/helpers/loaders.py

import io
import json
import base64
from typing import Any, Dict

import requests
import pandas as pd
import pdfplumber


def _download_bytes(url: str) -> bytes:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.content


def load_csv(url: str, max_rows: int = 200) -> Dict[str, Any]:
    """
    Download a CSV and return a JSON-safe representation:
    {
      "columns": [...],
      "dtypes": {...},
      "rows": [ {col: value, ...}, ... ]
    }
    """
    content = _download_bytes(url)
    buf = io.BytesIO(content)
    df = pd.read_csv(buf)

    return {
        "source": url,
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "rows": df.head(max_rows).to_dict(orient="records"),
        "row_count": int(len(df)),
    }


def load_pdf(url: str, max_pages: int = 10) -> Dict[str, Any]:
    """
    Download a PDF and extract text (first few pages).
    """
    content = _download_bytes(url)
    buf = io.BytesIO(content)

    texts = []
    with pdfplumber.open(buf) as pdf:
        for i, page in enumerate(pdf.pages):
            if i >= max_pages:
                break
            texts.append(page.extract_text() or "")

    joined_text = "\n\n".join(texts)

    return {
        "source": url,
        "pages_used": min(max_pages, len(texts)),
        "text": joined_text,
    }


def load_json(url: str) -> Dict[str, Any]:
    """
    Download JSON and return the parsed object.
    """
    content = _download_bytes(url)
    text = content.decode("utf-8", errors="replace")
    data = json.loads(text)
    return {
        "source": url,
        "data": data,
    }


def load_text(url: str, max_chars: int = 20000) -> Dict[str, Any]:
    """
    Download generic text (or HTML) and return as a string.
    """
    content = _download_bytes(url)
    text = content.decode("utf-8", errors="replace")
    if len(text) > max_chars:
        text = text[:max_chars]
    return {
        "source": url,
        "text": text,
    }


def load_image(url: str) -> Dict[str, Any]:
    """
    Download an image and return base64 data URI.
    """
    content = _download_bytes(url)
    b64 = base64.b64encode(content).decode("ascii")
    # Guess PNG/JPEG etc is okay; quizzes mainly care that it's image/*.
    data_uri = f"data:image/*;base64,{b64}"

    return {
        "source": url,
        "data_uri": data_uri,
    }
