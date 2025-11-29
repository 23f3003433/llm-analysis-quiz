# app/solver/llm_client.py

import os
from typing import Optional

from openai import OpenAI


class LLMClient:
    """
    Minimal wrapper around OpenAI Chat Completions.

    Expects:
      - env var OPENAI_API_KEY
      - optional env var LLM_MODEL (default: gpt-4.1-mini)
    """

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("LLM_MODEL", "gpt-4.1-mini")

    def chat(self, system: str, user: str, temperature: float = 0.0) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        return resp.choices[0].message.content


llm: Optional[LLMClient] = LLMClient()
