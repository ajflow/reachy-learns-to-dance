# Reachy Learns to Dance 🤖🕺

### Teach a robot to dance from any TikTok video in under 60 seconds

> **Built for the [Mistral AI Worldwide Hackathon 2026](https://mistral.ai)**
> 
> An AI agent skill that watches humans dance on TikTok, understands the choreography using computer vision, and replays it on a real robot — a [Reachy Mini](https://www.pollen-robotics.com/reachy-mini/) by Pollen Robotics.

<p align="center">
  <img src="https://img.shields.io/badge/Mistral_AI-Hackathon_2026-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/MediaPipe-Pose-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Reachy_Mini-Robot-red?style=for-the-badge" />
</p>

---

## 🎬 Demo

> *Video coming soon — watch Reachy Mini bust a move!*

https://github.com/user-attachments/assets/placeholder

---

## 💡 How It Works

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────┐
│   TikTok     │────▶│  MediaPipe Pose   │────▶│  Joint Mapping  │────▶│  Reachy Mini │
│   Video      │     │  Extraction       │     │  & Smoothing    │     │  Playback    │
│              │     │                   │     │                 │     │              │
│  Download    │     │  33 body landmarks │     │  Head → Head    │     │  REST API    │
│  via tikwm   │     │  per frame @10fps │     │  Torso → Body   │     │  WiFi control│
│              │     │                   │     │  Arms → Antennas│     │              │
└──────────────┘     └──────────────────┘     └─────────────────┘     └──────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   Mistral AI    │
                                              │                 │
                                              │  Dance analysis │
                                              │  Beat detection │
                                              │  Choreography   │
                                              │  generation     │
                                              └─────────────────┘
```

### The Pipeline

1. **📥 Download** — Grab any TikTok video by URL (via tikwm.com API)
2. **🔍 Pose Extraction** — MediaPipe Pose Landmarker detects 33 body keypoints per frame
3. **🎯 Joint Mapping** — Human skeleton maps to Reachy Mini's degrees of freedom:
   - **Head position** → Head yaw, pitch, roll
   - **Torso rotation** → Body yaw
   - **Arm raises** → Antenna angles
4. **🧹 Smoothing** — Moving average filter removes jitter from noisy pose data
5. **🎵 BPM Detection** — Estimates music tempo from motion oscillation frequency
6. **🤖 Playback** — Sends choreography as timed REST API calls to the robot

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- A [Reachy Mini](https://www.pollen-robotics.com/reachy-mini/) robot on your local network
- ~30MB disk space for the pose model (auto-downloads on first run)

### Install

```bash
git clone https://github.com/ajflow/reachy-learns-to-dance.git
cd reachy-learns-to-dance
pip install -r requirements.txt
```

### Usage

```bash
# 1. Extract dance from a TikTok video
python scripts/tiktok-to-dance.py --url "https://www.tiktok.com/@charlidamelio/video/123" --preview

# 2. Play it on your robot!
python scripts/reachy-dance.py --choreo dance_choreo.json

# From a local video file with amplified moves
python scripts/tiktok-to-dance.py --file dance.mp4 --amplify 1.5 --output my_dance.json

# Or use the 7 built-in dances
python scripts/reachy-dance.py --dance disco --bpm 120 --duration 15
python scripts/reachy-dance.py --list  # See all options
```

### Configuration

Set your robot's address:
```bash
export REACHY_HOST=192.168.1.42  # or reachy-mini.local
```

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Pose Extraction** | [MediaPipe Pose Landmarker](https://developers.google.com/mediapipe/solutions/vision/pose_landmarker) (Heavy model) |
| **Video Processing** | OpenCV |
| **AI Analysis** | [Mistral AI](https://mistral.ai) — dance style analysis & choreography generation |
| **Robot Control** | Reachy Mini REST API over WiFi |
| **Language** | Python 3.10+ |
| **Math** | NumPy — joint angle calculations & signal smoothing |

---

## 📁 Project Structure

```
reachy-learns-to-dance/
├── scripts/
│   ├── tiktok-to-dance.py    # TikTok → choreography pipeline
│   ├── reachy-dance.py        # Dance player + 7 built-in routines
│   ├── reachy-control.py      # Low-level robot control
│   └── setup-tunnel.sh        # Network tunnel helper
├── references/
│   └── api-reference.md       # Reachy Mini API docs
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 🎯 What Makes This Special

- **Zero choreography skills needed** — point it at any dance video and the robot learns
- **Under 60 seconds** end-to-end: download → extract → map → dance
- **Works with any human dance video** — TikTok, local files, webcam recordings
- **Motion amplification** — subtle human moves become expressive robot gestures
- **BPM-aware** — automatically syncs to the music's tempo
- **7 built-in dances** as fallbacks: disco, headbang, groovy, chicken, robot, celebrate, nod-along

---

## 🏗 Built With

This project was built as an [OpenClaw](https://openclaw.ai) AI agent skill — meaning an AI agent can autonomously:
1. Receive a TikTok URL from a user
2. Run the full pipeline
3. Make the robot dance
4. All through natural language conversation

---

## 👤 Team

**AJ Awan** — [Flowtivity](https://flowtivity.ai)
- AI consultant & builder
- Previously EY Manager, IT Advisory
- TOGAF 9 certified enterprise architect

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

<p align="center">
  <b>Built with ❤️ and 🤖 for the Mistral AI Worldwide Hackathon 2026</b>
</p>
