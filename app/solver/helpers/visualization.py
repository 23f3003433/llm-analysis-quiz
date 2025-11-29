# app/solver/helpers/visualization.py

from typing import Any, Dict, Optional

import io
import base64

import matplotlib.pyplot as plt
import pandas as pd


def _figure_to_data_uri() -> str:
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close()
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def build_visualization(results: Dict[str, Any]) -> str:
    """
    Build a simple chart from the available data.

    Heuristics:
    1. If 'analysis' has numeric_summary for some CSV, plot mean values.
    2. Else, if 'csv' exists, take first numeric column and plot its values.
    3. Else, create a dummy plot so the caller still gets a valid image.

    Returns a data URI (data:image/png;base64,...)
    """
    # Case 1: analysis with numeric summary
    analysis = results.get("analysis") or {}
    csv_analysis = analysis.get("csv") or {}

    for src, summary in csv_analysis.items():
        numeric_summary = summary.get("numeric_summary")
        if numeric_summary:
            # numeric_summary: {col: {stat: value, ...}, ...}
            means = {col: stats.get("mean") for col, stats in numeric_summary.items()}
            # Drop Nones
            means = {k: v for k, v in means.items() if v is not None}

            if means:
                plt.figure()
                cols = list(means.keys())
                vals = [means[c] for c in cols]
                plt.bar(cols, vals)
                plt.xticks(rotation=45, ha="right")
                plt.title("Mean of numeric columns")
                plt.tight_layout()
                return _figure_to_data_uri()

    # Case 2: raw CSV rows
    csv_dict = results.get("csv") or {}
    for src, payload in csv_dict.items():
        rows = payload.get("rows", [])
        df = pd.DataFrame(rows)
        if df.empty:
            continue

        numeric_df = df.select_dtypes(include=["number"])
        if numeric_df.empty:
            continue

        col = numeric_df.columns[0]
        plt.figure()
        plt.plot(numeric_df[col].values)
        plt.title(f"Line plot of {col} from {src}")
        plt.xlabel("Index")
        plt.ylabel(col)
        plt.tight_layout()
        return _figure_to_data_uri()

    # Case 3: fallback dummy plot
    plt.figure()
    plt.text(0.5, 0.5, "No numeric data available", ha="center", va="center")
    plt.axis("off")
    return _figure_to_data_uri()
