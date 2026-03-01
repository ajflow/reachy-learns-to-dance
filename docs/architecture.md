# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────┐
│                   Reachy Mini Robot                  │
│                                                      │
│  ┌──────────┐   ┌──────────────┐   ┌──────────────┐ │
│  │ Built-in │──>│ AudioEngine  │──>│  Dance Loop  │ │
│  │   Mic    │   │ (16kHz mono) │   │   (100Hz)    │ │
│  └──────────┘   └──────┬───────┘   └──────┬───────┘ │
│                        │                   │         │
│                        v                   v         │
│                 ┌──────────────┐   ┌──────────────┐  │
│                 │ MistralBrain │   │  20 Dance    │  │
│                 │  (8s async)  │   │    Moves     │  │
│                 └──────────────┘   └──────────────┘  │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │  Web Dashboard (port 8001)                   │    │
│  │  Waveform | BPM | Mood | Spectrum | Moves    │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
                        │
                        v (every 8 seconds)
                 ┌──────────────┐
                 │  Mistral AI  │
                 │   (Small)    │
                 └──────────────┘
```

## Components

### AudioEngine (`audio_engine.py`)

Real-time audio analysis running on the Pi's built-in microphone.

- **Input**: 16kHz mono audio from `reachymini_audio_src` (device 2)
- **Onset detection**: Energy-ratio based (1.5x average threshold), debounced at 150ms
- **BPM estimation**: Histogram clustering of onset intervals, updated every 2 seconds
- **Spectral analysis**: FFT-based frequency band decomposition
  - Bass: < 300 Hz
  - Mids: 300 - 2000 Hz
  - Treble: > 2000 Hz
- **Mood estimation**: Heuristic from energy level + spectral centroid
- **Silence detection**: 0.012 RMS threshold, robot idles after 2 seconds of silence

### MistralBrain (`mistral_brain.py`)

AI-powered mood classification using Mistral Small.

- **Input**: Audio features (BPM, energy, spectral centroid, current mood estimate)
- **Output**: Mood classification (chill/happy/intense/funky) + energy scale (0.3 to 1.0)
- **Frequency**: Every 8 seconds, non-blocking (runs in background thread)
- **Fallback**: If no API key or API errors, uses AudioEngine's spectral heuristics
- **Model**: `mistral-small-latest`

### Dance Loop (`main.py`)

The core control loop running at 100Hz.

1. Read audio state from AudioEngine
2. Consult MistralBrain for mood classification
3. Select move from mood-appropriate pool
4. Call move function with beat-synced time parameter
5. Apply position/orientation offsets to neutral pose
6. Send to robot via `set_target()`
7. Switch moves every 8 beats

### Move System

Uses `reachy_mini_dances_library` (v0.2.1) which provides 20 professional moves:

| Move | Style | Best For |
|------|-------|----------|
| simple_nod | Gentle | Chill, ambient |
| head_tilt_roll | Smooth | Chill, jazz |
| yeah_nod | Bouncy | Happy, pop |
| jackson_square | Sharp | Intense, EDM |
| groovy_sway_and_roll | Groovy | Funky, R&B |
| chicken_peck | Playful | Happy, fun |
| headbanger_combo | Aggressive | Intense, rock |
| ... | ... | ... |

Each move function takes `t_beats` (float) and returns `MoveOffsets`:
- `position_offset`: numpy array [x, y, z] in meters
- `orientation_offset`: numpy array [roll, pitch, yaw] in radians
- `antennas_offset`: numpy array [left, right] in radians

### Web Dashboard (`static/index.html`)

Single-page dashboard polling `/api/state` at 5Hz:

- Real-time volume waveform (canvas)
- BPM display with confidence percentage
- Mood badge with color coding
- Spectral analysis bars (bass/mids/treble)
- Current move name
- Move history timeline
- Mistral AI status and reasoning

## Mood-to-Move Mapping

```python
MOOD_MOVES = {
    "chill":   ["simple_nod", "head_tilt_roll", "side_to_side_sway",
                "chin_lead", "pendulum_swing"],
    "happy":   ["yeah_nod", "uh_huh_tilt", "chicken_peck",
                "side_peekaboo", "groovy_sway_and_roll", "side_to_side_sway"],
    "intense": ["jackson_square", "polyrhythm_combo", "interwoven_spirals",
                "grid_snap", "neck_recoil", "sharp_side_tilt"],
    "funky":   ["groovy_sway_and_roll", "side_glance_flick",
                "stumble_and_recover", "sharp_side_tilt", "dizzy_spin"],
}
```

## Safety

- **Body yaw locked to 0**: Body rotation causes the robot to fall over. All movement is head + antennas only.
- **Amplitude scaling**: `min(1.0, 0.4 + energy * 0.6)` prevents excessive movement at low volumes while allowing full range at high energy.
- **Silence timeout**: Robot returns to neutral pose after 2 seconds of no music.
