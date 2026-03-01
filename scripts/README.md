# Scripts

Standalone utility scripts used during development. These are NOT part of the HuggingFace app.

| Script | Purpose |
|--------|---------|
| `reachy-control.py` | Remote robot control via REST API (testing/debugging) |
| `reachy-dance.py` | Send choreographed dance sequences via goto endpoints |
| `tiktok-to-dance.py` | Extract dance moves from TikTok videos using MediaPipe |
| `setup-tunnel.sh` | Set up reverse SSH tunnel from Pi to VPS |

## Requirements

```bash
pip install mediapipe opencv-python-headless requests numpy
```
