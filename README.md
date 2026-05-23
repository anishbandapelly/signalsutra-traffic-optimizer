# SignalSutra — Hardware Integrated Build

**Voice-Assisted Quantum-Inspired Green-Time Budget Optimizer for Bengaluru Traffic Control**

SignalSutra converts a traffic officer's field update into a fair 10-minute green-time signal plan across connected Bengaluru junctions.

> **Important:** The polished UI is for **control-room analysis and approval**. Field traffic officers use the **ESP32-S3 voice wearable** with LED/audio feedback, not a screen.

---

## What is included

```text
signalsutra_hardware_integrated/
├── api_server.py                         # FastAPI bridge for ESP32 / ElatoAI transcripts
├── control_room_live.py                  # Live Streamlit dashboard reading latest hardware plan
├── app.py                                # Original polished manual/demo Streamlit dashboard
├── optimizer.py                          # Quantum-inspired simulated annealing optimizer
├── voice_parser.py                       # Deterministic field command parser
├── data.py                               # Bengaluru junction demo data
├── runtime_store.py                      # JSON runtime store for latest plan/device status
├── hardware/
│   └── signalsutra_field_unit_platformio/ # ESP32-S3 PlatformIO firmware
├── integrations/
│   └── elatoai/                          # ElatoAI bridge code + tool schema + instructions
├── docs/
│   ├── HARDWARE_SOFTWARE_SETUP.md        # Full setup guide
│   ├── API_CONTRACT.md                   # API request/response contract
│   ├── PITCH_COPY.md
│   └── QUANTUM_EXPLAINER.md
├── sample_data/junction_data.csv
├── static_control_room/index.html        # Standalone HTML demo UI
└── scripts/                              # Windows/macOS/Linux helper scripts
```

---

## Final architecture

```text
Traffic Officer
   ↓ speaks
ESP32-S3 Field Unit / ElatoAI Voice Wearable
   ↓ transcript over Wi-Fi
SignalSutra FastAPI Bridge
   ↓ parse + optimize
Micro Traffic Digital Twin + Ripple Score + Fairness Guard
   ↓
Quantum-Inspired Simulated Annealing Optimizer
   ↓
Green-Time Budget Plan
   ↓
Control Room Dashboard + Human Approval
```

---

## Fastest working demo

### 1. Start backend

```bash
pip install -r requirements.txt
uvicorn api_server:app --host 0.0.0.0 --port 8001 --reload
```

Test:

```text
http://127.0.0.1:8001/health
```

### 2. Start live dashboard

Open a second terminal:

```bash
streamlit run control_room_live.py
```

### 3. Flash ESP32-S3 firmware

Open this folder in VS Code PlatformIO:

```text
hardware/signalsutra_field_unit_platformio
```

Edit:

```text
src/Config.cpp
```

Set your Wi-Fi and laptop IP:

```cpp
const char* WIFI_SSID = "YOUR_WIFI_OR_PHONE_HOTSPOT";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* BACKEND_HOST = "192.168.1.100"; // laptop IP
const uint16_t BACKEND_PORT = 8001;
```

Build + Upload.

Press the ESP32 button. The backend should receive the transcript, generate a plan, and the live dashboard should show it.

---

## ElatoAI voice mode

The direct firmware mode proves the hardware-to-software connection. For real microphone-based voice:

1. Use ElatoAI `firmware-arduino` on the ESP32-S3.
2. Set ElatoAI `src/Config.cpp` server values to your laptop/server IP.
3. Add `integrations/elatoai/signalsutra_bridge.ts` to the ElatoAI server layer.
4. When ElatoAI has a final STT transcript, POST it to:

```text
http://<SIGNALSUTRA_IP>:8001/api/elatoai/transcript
```

SignalSutra returns the optimizer output and a short `speaker_text` for the ESP32 speaker.

---

## API test without hardware

```bash
curl -X POST http://127.0.0.1:8001/api/traffic-command \
  -H "Content-Type: application/json" \
  -d '{"transcript":"Heavy congestion at Madiwala toward Silk Board. Queue is spilling back toward BTM and Dairy Circle. Optimize signal flow for the next 10 minutes.","source":"test"}'
```

Expected result:

- status: `plan_ready`
- ripple score: `76 → 49`
- congestion reduction: about `35%`
- signal genome: `[+30, +30, +15, 0, 0, -10]` style allocation
- approval status: `pending`

---

## Why this is not just a dashboard

SignalSutra is a traffic control decision-support system:

- It does not tell commuters which route to take.
- It helps traffic officers allocate limited green-light seconds.
- It compares static timing, greedy local fix, and SignalSutra optimized plan.
- It uses fairness constraints so side roads are not blindly starved.
- It requires human approval before execution.

---

## Quantum-inspired component

Traffic signal timing is modeled as a combinatorial optimization problem. Each possible signal timing plan is represented as a **signal genome**. The optimizer searches possible genomes using simulated annealing:

```text
accept_probability = exp(-(new_cost - current_cost) / temperature)
temperature = temperature * cooling_rate
```

This is quantum-inspired/annealing-style search for a hackathon MVP, not a claim of running on quantum hardware.

---

## Demo command

```text
Heavy congestion at Madiwala toward Silk Board. Queue is spilling back toward BTM and Dairy Circle. Optimize signal flow for the next 10 minutes.
```

---

## Main demo result

```text
Before Ripple Score: 76
After Ripple Score: 49
Congestion Reduction: 35%
Average Wait: 92 sec → 61 sec
Human Approval: Required
```

---

## More setup details

Read:

```text
docs/HARDWARE_SOFTWARE_SETUP.md
docs/API_CONTRACT.md
integrations/elatoai/README.md
```

---

## Presentation deck

The pitch presentation deck is included here:

```text
[SignalSutra_Pitch_Deck (1)  -  Repaired.pdf](https://github.com/user-attachments/files/28175993/SignalSutra_Pitch_Deck.1.-.Repaired.pdf)

```

Deck coverage:

- Problem statement
- Proposed approach
- Hardware + software architecture
- Quantum-inspired optimization logic
- Demo workflow
- Real-world impact
- GitHub/codebase structure

---

## GitHub upload

This folder is GitHub-ready. After installing GitHub CLI and logging in, run one of these from the repo root:

Windows PowerShell:

```powershell
.\scripts\create_github_repo.ps1 -RepoName signalsutra-traffic-optimizer
```

macOS/Linux:

```bash
bash scripts/create_github_repo.sh signalsutra-traffic-optimizer
```

Or upload using GitHub Desktop by creating a new repository from this folder.
