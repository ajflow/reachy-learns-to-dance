# Reachy Learns to Dance 🤖🎶

A HuggingFace Reachy Mini App that listens to live music through the robot's built-in microphone and dances in real-time, with Mistral AI choosing the dance style based on what it hears.

**Built for the Mistral Worldwide Hackathon 2026** | Track 2: Anything Goes

## Demo

[Watch the demo on Loom](https://www.loom.com/share/7a5b99a37c4e4c9881c137d049379fdd)

## What It Does

1. **Listens** to ambient music through the Reachy Mini's built-in microphone
2. **Analyzes** audio in real-time: BPM detection, energy tracking, spectral mood estimation
3. **Asks Mistral AI** every 8 seconds: "What kind of music is this? How should I dance?"
4. **Dances** using 20 professional moves from the `reachy_mini_dances_library`, matched to the mood Mistral detects
5. **Shows its thinking** on a live web dashboard: waveform, BPM, mood, spectral analysis, move history

Zero configuration. Turn it on, play music, watch it groove.

## How Mistral AI Fits In

The robot's audio engine extracts features (BPM, energy, spectral centroid, bass/treble ratio) and sends them to **Mistral Small** every 8 seconds. Mistral classifies the music into one of four moods:

| Mood | When Mistral Picks It | Dance Style |
|------|----------------------|-------------|
| Chill | Slow tempo, ambient, jazz, lo-fi | Gentle nods, soft swaying |
| Happy | Pop, dance, upbeat rhythms | Bouncy, playful movements |
| Intense | Rock, EDM, fast beats | Sharp, powerful moves |
| Funky | R&B, soul, groove-heavy bass | Rhythmic, groovy patterns |

Mistral also sets an `energy_scale` (0.3 to 1.0) controlling how big the movements are. The AI runs in a background thread so it never blocks the 100Hz dance loop.

Without a Mistral API key, the app falls back to spectral-based mood detection. With Mistral, the classifications are dramatically better because it understands musical context, not just frequency distributions.

## The "Agent With Taste" Angle

This entire project was built by an AI agent (Flowbee, running on OpenClaw) controlling the robot remotely over SSH. The agent:

- Extracted 3,642 dance moves from 10 TikTok videos to learn vocabulary
- Discovered the correct microphone device by testing each one
- Figured out the undocumented API fields through trial and error
- Built the audio engine, Mistral integration, web dashboard, and HuggingFace packaging
- Deployed and tested on the physical robot via reverse SSH tunnel from an AWS VPS

An AI agent that builds a dancing robot that uses AI to pick its dance moves. It's AI all the way down.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Reachy Mini                     │
│                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐ │
│  │ Built-in │──>│  Audio   │──>│  Dance Loop  │ │
│  │   Mic    │   │  Engine  │   │   (100Hz)    │ │
│  └──────────┘   └────┬─────┘   └──────┬───────┘ │
│                      │                │          │
│                      v                v          │
│               ┌──────────┐    ┌──────────────┐   │
│               │ Mistral  │    │  20 Pro      │   │
│               │  Brain   │    │  Dance Moves │   │
│               │ (8s poll)│    │  (library)   │   │
│               └──────────┘    └──────────────┘   │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │  Web Dashboard (port 8001)               │    │
│  │  Waveform | BPM | Mood | Spectral | Moves│    │
│  └──────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
                      │
                      v (every 8s)
              ┌──────────────┐
              │  Mistral AI  │
              │  (Small)     │
              │  api.mistral │
              └──────────────┘
```

## Installation

This is a standard HuggingFace Reachy Mini App. Install it on your robot:

```bash
# SSH into your Reachy Mini
ssh pollen@reachy-mini.local

# Clone and install
git clone https://github.com/ajflow/reachy-learns-to-dance.git
cd reachy-learns-to-dance
pip install -e .

# Set your Mistral API key (optional but recommended)
echo 'export MISTRAL_API_KEY=your-key-here' >> ~/.bashrc

# Toggle ON from the Reachy Mini dashboard/mobile app
```

The app appears in your Reachy Mini dashboard's Applications list. Toggle it ON, play some music, and watch it dance.

## Configuration

**None required.** The app auto-detects the microphone, estimates BPM from onset detection, and picks moves that match the mood.

Optional: Set `MISTRAL_API_KEY` environment variable for AI-powered mood classification instead of spectral heuristics.

## Web Dashboard

When the app is running, visit `http://reachy-mini.local:8001` to see:

- **Real-time waveform** of what the mic picks up
- **Volume meter** with peak tracking
- **BPM display** with confidence percentage
- **Auto-detected mood badge** (chill/happy/intense/funky)
- **Spectral analysis bars** (bass/mids/treble)
- **Current dance move** being executed
- **Move history** timeline
- **Mistral AI status** showing its mood reasoning

## How the Audio Engine Works

- **Onset detection**: Energy-ratio based (1.5x average = beat), debounced at 150ms
- **BPM estimation**: Histogram-based clustering of onset intervals, updated every 2 seconds
- **Spectral mood**: FFT-based analysis of bass (<300Hz), mids (300-2000Hz), treble (>2000Hz)
- **Energy tracking**: Smoothed volume with peak tracking, mapped to movement amplitude
- **Silence detection**: Threshold-based (0.012 RMS), robot goes idle after 2 seconds of silence

## Tech Stack

- **Robot**: Reachy Mini by Pollen Robotics (HuggingFace)
- **AI**: Mistral Small via Mistral AI API
- **Audio**: sounddevice + numpy FFT (no heavy ML dependencies)
- **Moves**: reachy_mini_dances_library v0.2.1 (20 professional moves)
- **Dashboard**: Vanilla HTML/CSS/JS, no build step
- **Packaging**: Standard Python package with HuggingFace Reachy Mini entry points

## Project Structure

```
reachy-learns-to-dance/
├── reachy_mini_dj/           # The HuggingFace Reachy Mini App
│   ├── main.py               # Dance loop + ReachyMiniDJ app class
│   ├── audio_engine.py       # Real-time audio analysis (BPM, mood, energy)
│   ├── mistral_brain.py      # Mistral AI mood classification
│   ├── static/index.html     # Live web dashboard
│   ├── __main__.py           # Module entry point
│   └── __init__.py
├── data/tiktok-dances/       # 3,642 keyframes from 10 TikTok videos
├── scripts/                  # Dev utilities (remote control, TikTok extraction)
├── docs/
│   ├── architecture.md       # System design and component details
│   └── how-it-was-built.md   # The story of an AI agent building a dancing robot
├── pyproject.toml            # Package config with HuggingFace entry points
└── README.md
```

## Documentation

- [Architecture](docs/architecture.md): System design, component details, mood-to-move mapping
- [How It Was Built](docs/how-it-was-built.md): The story of an AI agent building this project remotely over SSH

## License

MIT

## Credits

Built by AJ Awan ([Flowtivity](https://flowtivity.ai)) and Flowbee (AI agent running on [OpenClaw](https://github.com/openclaw/openclaw)) for the Mistral Worldwide Hackathon 2026.
