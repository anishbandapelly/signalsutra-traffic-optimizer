"""Simple voice/manual command parser for the hackathon MVP.

In Phase 2 this can be replaced with an STT + LLM/NLU parser. For the demo we
keep it deterministic and transparent so judges can see exactly what is parsed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict

DEFAULT_COMMAND = (
    "Heavy congestion at Madiwala toward Silk Board. Queue is spilling back "
    "toward BTM and Dairy Circle. Optimize signal flow for the next 10 minutes."
)

@dataclass
class ParsedCommand:
    location: str = "Madiwala"
    direction: str = "Toward Silk Board"
    connected_pressure: list[str] | None = None
    time_window: str = "10 minutes"
    mode: str = "Peak-hour decongestion"
    raw_text: str = DEFAULT_COMMAND

    def to_dict(self) -> dict:
        data = asdict(self)
        if data["connected_pressure"] is None:
            data["connected_pressure"] = ["BTM", "Dairy Circle"]
        return data

def parse_command(text: str | None) -> dict:
    """Parse a field officer's voice update into structured demo fields."""
    raw = (text or DEFAULT_COMMAND).strip()
    lower = raw.lower()

    location = "Madiwala"
    for candidate in ["Madiwala", "Silk Board", "BTM", "Dairy Circle", "Koramangala"]:
        if candidate.lower() in lower:
            location = candidate if candidate != "Silk Board" else "Silk Board Approach"
            break

    direction = "Toward Silk Board" if "silk" in lower else "Toward connected corridor"

    pressure = []
    for name in ["BTM", "Dairy Circle", "Koramangala", "Side Road"]:
        if name.lower() in lower and name not in pressure and name.lower() not in location.lower():
            pressure.append(name)
    if not pressure:
        pressure = ["BTM", "Dairy Circle"]

    match = re.search(r"(next|for)?\s*(\d+)\s*(minute|min|minutes|mins)", lower)
    time_window = f"{match.group(2)} minutes" if match else "10 minutes"

    return ParsedCommand(
        location=location,
        direction=direction,
        connected_pressure=pressure,
        time_window=time_window,
        mode="Peak-hour decongestion",
        raw_text=raw,
    ).to_dict()
