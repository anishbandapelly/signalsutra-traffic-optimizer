"""Small JSON runtime store used by the FastAPI bridge and live dashboard.

This keeps the hackathon MVP simple: the ESP32/ElatoAI bridge posts a voice
transcript, the backend writes the latest optimizer result to runtime/latest_plan.json,
and the control-room dashboard can read it without a database.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = ROOT_DIR / "runtime"
LATEST_PLAN_PATH = RUNTIME_DIR / "latest_plan.json"
DEVICE_STATUS_PATH = RUNTIME_DIR / "device_status.json"
EVENTS_PATH = RUNTIME_DIR / "events.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_runtime_dir() -> None:
    RUNTIME_DIR.mkdir(exist_ok=True)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_runtime_dir()
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def append_event(event_type: str, payload: dict[str, Any]) -> None:
    ensure_runtime_dir()
    row = {"time": utc_now(), "type": event_type, **payload}
    with EVENTS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_events(limit: int = 50) -> list[dict[str, Any]]:
    if not EVENTS_PATH.exists():
        return []
    lines = EVENTS_PATH.read_text(encoding="utf-8").splitlines()[-limit:]
    out: list[dict[str, Any]] = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def default_device_status() -> dict[str, Any]:
    return {
        "device_id": "signalsutra-field-unit-01",
        "device": "SignalSutra ESP32-S3 Field Unit",
        "connection": "Waiting for hardware",
        "battery": "82%",
        "led": "Green",
        "led_meaning": "Standby",
        "mode": "Peak-hour optimization",
        "updated_at": utc_now(),
    }
