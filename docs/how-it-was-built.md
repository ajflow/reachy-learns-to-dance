# How It Was Built

This entire project was built by an AI agent (Flowbee, running on [OpenClaw](https://github.com/openclaw/openclaw)) controlling the physical robot remotely. Here is the story.

## The Setup

- **VPS**: AWS EC2 in Sydney running the AI agent
- **Robot**: Reachy Mini (wireless version) on a home WiFi network
- **Connection**: Reverse SSH tunnel from Pi to VPS (ports 8000 for API, 2222 for SSH, 8001 for dashboard)

The agent never physically touched the robot. Everything was done over SSH and the REST API.

## Discovery Phase

The agent started with zero knowledge of the Reachy Mini platform. Through exploration:

1. **Found the mic**: Tested all audio devices, discovered device 0 (pipewire) was silent and device 2 (`reachymini_audio_src`) was the actual microphone
2. **Found the API fields**: Initial attempts used `neck` (wrong) and `l_antenna/r_antenna` (wrong). Discovered the correct fields are `head_pose` and `antennas` array through trial and error
3. **Found the dance library**: Discovered `reachy_mini_dances_library` was already installed on the Pi with 20 professional moves
4. **Found the venv issue**: The daemon uses `/venvs/apps_venv/` for wireless robots, not `/venvs/mini_daemon/` where we initially installed

## TikTok Dance Extraction

To build a dance vocabulary:

1. Downloaded 10 TikTok dance videos using tikwm.com API
2. Extracted human poses using MediaPipe
3. Mapped body joint angles to Reachy Mini's head and antenna movements
4. Generated 3,642 keyframes across 10 choreographies
5. Stored as JSON with BPM and timing metadata

This data lives in `data/tiktok-dances/`.

## Audio Engine Development

The agent built the audio analysis pipeline iteratively:

- **v1**: Simple volume threshold for silence detection
- **v2**: Added onset-based beat detection with energy ratio threshold
- **v3**: Added BPM estimation via histogram clustering of onset intervals
- **v4**: Added spectral analysis (FFT) for mood estimation
- **v5**: Tuned thresholds for the Pi's specific microphone characteristics

Key insight: The Pi's built-in mic has different sensitivity than expected. Silence threshold of 0.012 RMS worked well, and onset threshold of 1.5x average energy was reliable for beat detection.

## The Falls

During testing, the robot fell over multiple times due to excessive body rotation. The agent learned to keep `body_yaw` at 0 and express all dancing through head movement and antennas only. Amplitude scaling was capped at safe levels.

## Packaging as HuggingFace App

The final step was packaging as a proper Reachy Mini app:

1. Created `pyproject.toml` with `reachy_mini_apps` entry point
2. Implemented `ReachyMiniDJ` class extending `ReachyMiniApp`
3. Added `custom_app_url` for the web dashboard
4. Installed in the correct venv (`/venvs/apps_venv/`)
5. Verified discovery through the daemon's entry point system

## Timeline

All of this was done in a single weekend hackathon session, with the AI agent working autonomously for long stretches while the human (AJ) provided direction and filmed demos.
