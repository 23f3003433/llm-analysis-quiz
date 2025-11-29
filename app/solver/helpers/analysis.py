# app/solver/helpers/analysis.py

from typing import Any, Dict

import pandas as pd


def clean_data(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Basic cleaning pass over loaded data.

    For now this mainly:
    - leaves everything as-is (no heavy mutations),
    - but returns a copy so future extensions can normalize,
      trim strings, handle nulls, etc.

    The LLM will see this cleaned structure in the prompt.
    """
    # Shallow copy is enough for our simple usage.
    cleaned = dict(results)
    return cleaned


def analyze_data(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate simple descriptive statistics over any CSV-like data.

    Input format (from loaders.load_csv):
    results["csv"] = {
        url: {
          "columns": [...],
          "rows": [ {...}, ... ],
          "row_count": n,
          ...
        },
        ...
    }

    Returns a JSON-safe summary that the LLM can use for
    more complex reasoning.
    """
    analysis: Dict[str, Any] = {}

    csv_dict = results.get("csv") or {}
    csv_summary: Dict[str, Any] = {}

    for src, payload in csv_dict.items():
        rows = payload.get("rows", [])
        df = pd.DataFrame(rows)

        summary: Dict[str, Any] = {
            "source": src,
            "row_count": payload.get("row_count", len(df)),
            "columns": list(df.columns),
        }

        if not df.empty:
            # Describe only numeric columns to keep size small
            numeric_df = df.select_dtypes(include=["number"])
            if not numeric_df.empty:
                desc = numeric_df.describe().to_dict()
                summary["numeric_summary"] = desc

        csv_summary[src] = summary

    if csv_summary:
        analysis["csv"] = csv_summary

    # You can extend here for PDF text analytics, API response stats, etc.
    # e.g., word counts, keyword frequencies, etc.

    return analysis
