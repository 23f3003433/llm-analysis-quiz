# app/solver/handlers/submit.py

import json
import httpx


async def submit_answer(
    submit_url: str,
    email: str,
    secret: str,
    answer
):
    """
    Submits the computed answer back to the quiz evaluation endpoint.

    Expected format:
    {
        "email":  "...",
        "secret": "...",
        "answer": <value>   # can be number / string / boolean / dict / base64 image
    }
    """

    payload = {
        "email": email,
        "secret": secret,
        "answer": answer
    }

    # Use a persistent async client for performance
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                submit_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            try:
                data = response.json()
            except Exception:
                data = {
                    "correct": False,
                    "reason": "Invalid JSON response from server",
                    "status_code": response.status_code,
                    "raw_text": response.text,
                }

            return data

    except Exception as e:
        return {
            "correct": False,
            "reason": f"Submit error: {str(e)}",
            "submit_url": submit_url,
        }
