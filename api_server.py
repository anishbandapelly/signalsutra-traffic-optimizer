"""SignalSutra hardware/software bridge API.

Run this on the laptop/control-room machine:
    uvicorn api_server:app --host 0.0.0.0 --port 8001 --reload

The ESP32-S3 or ElatoAI server posts a transcript to /api/traffic-command.
The API parses the command, runs the quantum-inspired optimizer, stores the
latest result, and returns a compact response for LED/audio feedback.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from data import DEFAULT_TIME_WINDOW_MINUTES, GREEN_BUDGET_SECONDS, load_junction_data
from optimizer import format_genome, run_annealing_optimizer
from runtime_store import (
    DEVICE_STATUS_PATH,
    LATEST_PLAN_PATH,
    append_event,
    default_device_status,
    read_events,
    read_json,
    utc_now,
    write_json,
)
from voice_parser import DEFAULT_COMMAND, parse_command


class TrafficCommandRequest(BaseModel):
    transcript: str = Field(default=DEFAULT_COMMAND, description="Final voice transcript from ESP32/ElatoAI")
    source: str = Field(default="esp32-direct", description="esp32-direct, elatoai, control-room, test")
    device_id: str = Field(default="signalsutra-field-unit-01")
    confidence: float | None = Field(default=None, description="Optional STT confidence score")


class DeviceStatusRequest(BaseModel):
    device_id: str = "signalsutra-field-unit-01"
    connection: str = "Connected"
    battery: str = "82%"
    led: str = "Green"
    led_meaning: str = "Standby"
    mode: str = "Peak-hour optimization"


class ApprovalRequest(BaseModel):
    approved_by: str = "Control Room Officer"
    notes: str = "Signal plan reviewed and approved."


app = FastAPI(
    title="SignalSutra Hardware Bridge API",
    version="2.0.0",
    description="ESP32-S3 / ElatoAI voice wearable bridge for SignalSutra control-room optimizer.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _df_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    cleaned = df.copy()
    for col in cleaned.columns:
        if cleaned[col].dtype.kind in "f":
            cleaned[col] = cleaned[col].round(2)
    return cleaned.to_dict(orient="records")


def build_signal_response(req: TrafficCommandRequest) -> dict[str, Any]:
    data = load_junction_data()
    parsed = parse_command(req.transcript)
    result = run_annealing_optimizer(data, iterations=2500, seed=42)

    response = {
        "status": "plan_ready",
        "timestamp": utc_now(),
        "source": req.source,
        "device_id": req.device_id,
        "transcript": req.transcript,
        "parsed_command": parsed,
        "hardware_feedback": {
            "led": "Green",
            "speaker_text": (
                "SignalSutra plan ready. Madiwala and Silk Board get extra green time. "
                "Control-room approval is required before execution."
            ),
        },
        "metrics": {
            "before_ripple": result.before_ripple,
            "after_ripple": result.after_ripple,
            "before_wait_seconds": result.before_wait,
            "after_wait_seconds": result.after_wait,
            "congestion_reduction_pct": round(result.congestion_reduction_pct, 2),
            "plan_confidence_pct": result.confidence_pct,
        },
        "optimizer": {
            "mode": "quantum-inspired simulated annealing",
            "iterations": result.iterations,
            "temperature_start": result.temperature_start,
            "cooling_rate": result.cooling_rate,
            "best_cost": round(result.best_cost, 3),
            "signal_genome": result.best_genome,
            "signal_genome_text": format_genome(result.best_genome),
            "green_budget_seconds": GREEN_BUDGET_SECONDS,
            "time_window_minutes": DEFAULT_TIME_WINDOW_MINUTES,
        },
        "signal_plan": _df_records(result.plan),
        "ripple_ranking": _df_records(result.ranking),
        "baseline_comparison": _df_records(result.baseline),
        "fairness_guard": {
            "minimum_green_time_maintained": True,
            "side_road_starvation_prevented": True,
            "no_unsafe_signal_reduction": True,
            "human_approval_required": True,
            "approval_status": "pending",
        },
        "logs": result.logs,
    }
    write_json(LATEST_PLAN_PATH, response)
    write_json(
        DEVICE_STATUS_PATH,
        {
            "device_id": req.device_id,
            "device": "SignalSutra ESP32-S3 Field Unit",
            "connection": "Connected",
            "battery": "82%",
            "led": "Green",
            "led_meaning": "Plan Ready",
            "mode": "Peak-hour optimization",
            "updated_at": utc_now(),
        },
    )
    append_event("plan_ready", {"source": req.source, "device_id": req.device_id, "genome": result.best_genome})
    return response


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "SignalSutra Hardware Bridge API",
        "health": "/health",
        "post_transcript": "/api/traffic-command",
        "latest_plan": "/api/latest-plan",
        "device_ws": "/ws/device",
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "time": utc_now(), "service": "signalsutra-api", "port": 8001}


@app.post("/api/traffic-command")
def traffic_command(req: TrafficCommandRequest) -> dict[str, Any]:
    return build_signal_response(req)


@app.post("/api/elatoai/transcript")
def elatoai_transcript(req: TrafficCommandRequest) -> dict[str, Any]:
    req.source = "elatoai"
    return build_signal_response(req)


@app.get("/api/demo-command")
def demo_command() -> dict[str, Any]:
    return build_signal_response(TrafficCommandRequest(source="control-room-demo"))


@app.get("/api/latest-plan")
def latest_plan() -> dict[str, Any]:
    plan = read_json(LATEST_PLAN_PATH)
    return plan or {"status": "no_plan_yet", "message": "No ESP32/ElatoAI command received yet."}


@app.post("/api/approve")
def approve_plan(req: ApprovalRequest) -> dict[str, Any]:
    plan = read_json(LATEST_PLAN_PATH)
    if not plan:
        return {"status": "no_plan_yet", "message": "Run optimizer before approval."}
    plan["fairness_guard"]["approval_status"] = "approved"
    plan["approval"] = {"approved_by": req.approved_by, "notes": req.notes, "approved_at": utc_now()}
    plan["hardware_feedback"] = {
        "led": "Green",
        "speaker_text": "Signal plan approved. Field unit notified. Execute only as per control-room protocol.",
    }
    write_json(LATEST_PLAN_PATH, plan)
    append_event("approved", {"approved_by": req.approved_by})
    return {"status": "approved", "approval": plan["approval"], "hardware_feedback": plan["hardware_feedback"]}


@app.get("/api/device-status")
def get_device_status() -> dict[str, Any]:
    return read_json(DEVICE_STATUS_PATH) or default_device_status()


@app.post("/api/device-status")
def post_device_status(req: DeviceStatusRequest) -> dict[str, Any]:
    payload = req.model_dump()
    payload.update({"device": "SignalSutra ESP32-S3 Field Unit", "updated_at": utc_now()})
    write_json(DEVICE_STATUS_PATH, payload)
    append_event("device_status", payload)
    return {"status": "stored", "device": payload}


@app.get("/api/events")
def events(limit: int = 50) -> dict[str, Any]:
    return {"events": read_events(limit)}


@app.websocket("/ws/device")
async def ws_device(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "connected", "message": "SignalSutra device bridge ready"})
    try:
        while True:
            msg = await websocket.receive_json()
            msg_type = msg.get("type", "transcript")
            if msg_type in {"transcript", "voice_command", "demo_command"}:
                req = TrafficCommandRequest(
                    transcript=msg.get("transcript") or DEFAULT_COMMAND,
                    source=msg.get("source", "esp32-websocket"),
                    device_id=msg.get("device_id", "signalsutra-field-unit-01"),
                    confidence=msg.get("confidence"),
                )
                response = build_signal_response(req)
                await websocket.send_json(response)
            elif msg_type == "status":
                status = DeviceStatusRequest(**{k: v for k, v in msg.items() if k in DeviceStatusRequest.model_fields})
                post_device_status(status)
                await websocket.send_json({"type": "status_ack", "time": utc_now()})
            else:
                await websocket.send_json({"type": "ack", "message": "Unknown message stored as event"})
                append_event("device_message", msg)
    except WebSocketDisconnect:
        append_event("device_disconnect", {"message": "ESP32 websocket disconnected"})
