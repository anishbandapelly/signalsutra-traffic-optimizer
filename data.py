"""Demo data and graph structure for SignalSutra.

The MVP uses simulated Bengaluru-style junction data so the hackathon demo is
reproducible without depending on live camera feeds or traffic APIs.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent
DATA_PATH = ROOT_DIR / "sample_data" / "junction_data.csv"

ACTION_SET = [-10, 0, 15, 30]
GREEN_BUDGET_SECONDS = 120
DEFAULT_TIME_WINDOW_MINUTES = 10

# Micro Bengaluru junction cluster used in the demo.
EDGES = [
    ("Madiwala", "Silk Board Approach"),
    ("Madiwala", "BTM Link"),
    ("Silk Board Approach", "Dairy Circle Link"),
    ("Silk Board Approach", "Koramangala Link"),
    ("BTM Link", "Dairy Circle Link"),
    ("Dairy Circle Link", "Koramangala Link"),
    ("BTM Link", "Side Road"),
    ("Dairy Circle Link", "Side Road"),
]

POSITIONS = {
    "Madiwala": (0.22, 0.56),
    "Silk Board Approach": (0.58, 0.78),
    "BTM Link": (0.10, 0.22),
    "Dairy Circle Link": (0.50, 0.20),
    "Koramangala Link": (0.82, 0.34),
    "Side Road": (0.27, 0.08),
}

def load_junction_data(path: str | Path = DATA_PATH) -> pd.DataFrame:
    """Load the demo junction data as a DataFrame."""
    df = pd.read_csv(path)
    numeric_cols = [
        "density", "wait_time", "queue_length", "connected_impact",
        "spillback_risk", "current_green", "min_green", "max_green",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col])
    return df
