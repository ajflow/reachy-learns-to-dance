# Hackiterate Submission: Reachy Learns to Dance

## Project Name
Reachy Learns to Dance

## Tagline
A robot that listens to live music and dances with AI-chosen style

## Description

Reachy Mini DJ is a HuggingFace Reachy Mini App that turns the robot into a music-responsive dancer. It listens through the built-in microphone, analyzes the audio in real-time (BPM, energy, spectral features), and uses Mistral AI to classify the mood of the music. Based on Mistral's classification, it picks from 20 professional dance moves that match the vibe: gentle swaying for jazz, headbanging for rock, groovy moves for funk.

The entire project was built by an AI agent (running on OpenClaw) that controlled the physical robot remotely via SSH reverse tunnel from an AWS server. The agent discovered the correct microphone device by testing each one, figured out undocumented API fields through trial and error, extracted 3,642 dance moves from 10 TikTok videos to build vocabulary, and deployed the final app to the robot.

### How Mistral AI is used

Every 8 seconds, the app sends audio features (BPM, energy level, spectral centroid, bass/treble ratio) to Mistral Small. Mistral classifies the music into one of four moods (chill, happy, intense, funky) and sets an energy scale controlling movement amplitude. This runs in a background thread so it never blocks the 100Hz dance control loop.

Without Mistral, the app falls back to spectral heuristics. With Mistral, the mood detection is dramatically better because it understands musical context beyond raw frequency distributions.

### Key Features
- Zero configuration: install the app, toggle ON, play music
- Real-time audio analysis with onset-based BPM detection
- Mistral AI mood classification (chill/happy/intense/funky)
- 20 professional dance moves matched to detected mood
- Live web dashboard showing the robot's musical interpretation
- Standard HuggingFace Reachy Mini App format (installable by anyone)

## Tech Stack
- Reachy Mini robot (HuggingFace / Pollen Robotics)
- Mistral Small (mood classification from audio features)
- Python (sounddevice, numpy FFT, no heavy ML deps)
- reachy_mini_dances_library (20 pro moves)
- Vanilla HTML/CSS/JS dashboard

## Links
- GitHub: https://github.com/ajflow/reachy-learns-to-dance
- Demo video: [TBD]

## Team
- AJ Awan (Flowtivity) + Flowbee (AI agent built on OpenClaw)
