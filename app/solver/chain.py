import json
import traceback
from urllib.parse import urlparse

from .fetch import fetch_html
from .parser import extract_submit_url
from .helpers import (
    load_csv,
    load_pdf,
    load_json,
    load_text,
    load_image,
    scrape_page,
    call_api,
    clean_data,
    analyze_data,
    build_visualization
)
from .llm_client import llm


def fallback_submit_url(url: str) -> str:
    """Used when no submit URL is found inside the HTML."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/submit"


async def solve_quiz_chain(req, quiz_url: str):
    """
    FULLY GENERIC QUIZ SOLVING PIPELINE
    ===================================

    Steps:
    1. Fetch HTML.
    2. Ask LLM to analyze quiz and create a plan:
        - required tools
        - required input URLs
        - steps
        - any API calls
    3. Execute these tools:
        - CSV / PDF / JSON loaders
        - scraper
        - API calls
        - text/image loaders
        - clean → analyze → visualize
    4. Send combined results back to LLM to compute final answer.
    5. Submit final answer.
    """

    try:
        # --------------------------------------------------------
        # 1. Fetch the quiz page HTML
        # --------------------------------------------------------
        html = await fetch_html(quiz_url)
        if html is None:
            return {"correct": False, "url": "", "reason": "Failed to fetch HTML"}

        # --------------------------------------------------------
        # 2. Ask LLM: What tools do we need? What inputs to load?
        # --------------------------------------------------------
        system_prompt = """
You are a QUIZ TASK ANALYZER.
Given a full quiz HTML page, produce a JSON plan describing:

{
 "task": "<summary of the question>",
 "inputs": [ list of downloadable links or API endpoints ],
 "tools": [ 
      "scrape", "csv", "pdf", "json", "text", 
      "image", "api", "clean", "analyze", "visualize"
 ],
 "api_url": "<if API call is needed, else null>"
}

Rules:
- DO NOT guess. Only identify tools present in the HTML.
- Inputs must include all relevant downloadable files.
- Tools may be used together (e.g. csv + analyze + visualize).
"""
        user_prompt = f"Analyze this quiz page and produce the tool plan:\n\n{html}"

        raw_plan = llm.chat(system=system_prompt, user=user_prompt)
        try:
            plan = json.loads(raw_plan)
        except:
            return {
                "correct": False,
                "url": "",
                "reason": "LLM plan is not valid JSON",
                "raw_plan": raw_plan
            }

        tools = plan.get("tools", [])
        inputs = plan.get("inputs", [])

        # --------------------------------------------------------
        # 3. Execute tools required
        # --------------------------------------------------------
        results = {}

        # (A) SCRAPING (fetch page content)
        if "scrape" in tools:
            results["scraped_page"] = await scrape_page(quiz_url)

        # (B) LOAD FILE INPUTS
        for link in inputs:
            try:
                if link.endswith(".csv"):
                    results.setdefault("csv", {})[link] = load_csv(link)

                elif link.endswith(".pdf"):
                    results.setdefault("pdf", {})[link] = load_pdf(link)

                elif link.endswith(".json"):
                    results.setdefault("json", {})[link] = load_json(link)

                elif link.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                    results.setdefault("image", {})[link] = load_image(link)

                else:
                    # assume generic text/HTML
                    results.setdefault("text", {})[link] = load_text(link)
            except Exception as e:
                results.setdefault("load_errors", {})[link] = str(e)

        # (C) API CALL
        if "api" in tools:
            api_url = plan.get("api_url")
            if api_url:
                try:
                    results["api_response"] = await call_api(api_url)
                except Exception as e:
                    results["api_error"] = str(e)

        # (D) CLEAN DATA
        if "clean" in tools:
            results["cleaned"] = clean_data(results)

        # (E) ANALYSIS
        if "analyze" in tools:
            results["analysis"] = analyze_data(results)

        # (F) VISUALIZATION
        if "visualize" in tools:
            try:
                results["image_b64"] = build_visualization(results)
            except Exception as e:
                results["visualization_error"] = str(e)

        # --------------------------------------------------------
        # 4. Ask LLM to compute final answer
        # --------------------------------------------------------
        final_prompt = f"""
You have executed a full data pipeline for a quiz.

Here is ALL extracted data and analysis (truncated to 7000 chars if too large):

{json.dumps(results)[:7000]}

Now compute the FINAL ANSWER to the quiz.

Return ONLY JSON:
{{
   "answer": <number | string | boolean | object | base64 image URI>
}}
"""

        final_raw = llm.chat(
            system="You are an accurate quiz solver.",
            user=final_prompt
        )

        try:
            final_json = json.loads(final_raw)
            answer = final_json["answer"]
        except Exception:
            return {
                "correct": False,
                "url": "",
                "reason": "Final LLM answer invalid JSON",
                "raw_final": final_raw
            }

        # --------------------------------------------------------
               # 5. Submit answer
        # --------------------------------------------------------
        from .helpers.submit import submit_answer

        submit_url = extract_submit_url(html) or fallback_submit_url(quiz_url)

        result = await submit_answer(
            submit_url,
            req.email,
            req.secret,
            answer
        )

        return {
            "correct": result.get("correct"),
            "url": result.get("url"),
            "reason": result.get("reason"),
            "answer_used": answer,
            "plan": plan
        }

    except Exception as e:
        return {
            "correct": False,
            "url": "",
            "reason": str(e),
            "trace": traceback.format_exc()
        }
