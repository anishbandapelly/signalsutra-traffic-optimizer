"""ESP32-S3 field unit status simulator.

In the real build, this file can read serial/MQTT/WebSocket status from the
wearable. In this MVP it keeps the hardware role visible without pretending the
optimizer runs on the microcontroller.
"""

from __future__ import annotations

def get_hardware_status(stage: str = "standby") -> dict:
    led_map = {
        "standby": ("Green", "Ready / standby"),
        "listening": ("Blue", "Listening to officer voice"),
        "optimizing": ("Yellow", "Backend optimizer running"),
        "severe": ("Red", "Severe congestion ripple"),
        "peak": ("Purple", "Peak-hour optimization mode"),
        "approved": ("Green", "Approved signal plan"),
    }
    led, meaning = led_map.get(stage, led_map["standby"])
    return {
        "device": "SignalSutra ESP32-S3 Field Unit",
        "interface": "Voice AI wearable — no screen UI for field officers",
        "connection": "Demo Mode",
        "battery": "82%",
        "mode": "Peak-hour decongestion",
        "led": led,
        "led_meaning": meaning,
        "backend_note": "Quantum-inspired optimizer runs on backend/control-room system, not on ESP32.",
    }
