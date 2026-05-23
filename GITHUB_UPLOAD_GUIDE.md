# GitHub Upload Guide — SignalSutra

This package is ready to become a GitHub repository.

## What must be uploaded

- `README.md`
- `presentation/SignalSutra_Pitch_Deck.pptx`
- Python demo codebase
- FastAPI hardware bridge
- Streamlit control-room dashboard
- PlatformIO ESP32-S3 firmware
- ElatoAI integration files
- Docs, assets, and sample data

## Option 1 — GitHub Desktop

1. Open GitHub Desktop.
2. File → Add local repository.
3. Choose this folder.
4. If asked, create repository.
5. Commit all files with message:

```text
Initial SignalSutra hardware-integrated demo
```

6. Publish repository.

## Option 2 — GitHub CLI

Install GitHub CLI, then run:

```bash
gh auth login
```

From this folder:

```bash
git init
git add .
git commit -m "Initial SignalSutra hardware-integrated demo"
gh repo create signalsutra-traffic-optimizer --public --source=. --remote=origin --push
```

## Suggested repository name

```text
signalsutra-traffic-optimizer
```

## Suggested repository description

```text
Voice-assisted quantum-inspired green-time budget optimizer for Bengaluru traffic control, with ESP32-S3 wearable hardware integration and control-room dashboard.
```
