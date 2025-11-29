# app/solver/helpers/api_tools.py

from typing import Any, Dict, Optional

import httpx


async def call_api(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    timeout: int = 60,
) -> Dict[str, Any]:
    """
    Generic async HTTP API caller.

    Used when the quiz page asks you to:
    - call some REST API
    - possibly pass specific headers
    - send a JSON payload

    Returns: {
      "url": ...,
      "status_code": ...,
      "headers": ...,
      "json": ... or None,
      "text": ...,
    }
    """
    method = method.upper()
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.request(method, url, headers=headers, json=json_body)

    result: Dict[str, Any] = {
        "url": url,
        "status_code": resp.status_code,
        "headers": dict(resp.headers),
    }

    try:
        result["json"] = resp.json()
    except Exception:
        result["json"] = None

    result["text"] = resp.text[:20000]  # truncate
    return result
