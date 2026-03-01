"""Mistral AI brain: analyzes music characteristics and picks dance style."""

import json
import os
import threading
import time
from typing import Optional

import requests

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

SYSTEM_PROMPT = """You are the AI brain of a dancing robot called Reachy Mini DJ. 
You receive audio analysis data from the robot's microphone (BPM, energy level, spectral features, mood estimate) and must decide which dance style fits the music best.

Available dance moods:
- "chill": Gentle, relaxed moves. Good for slow music, ambient, jazz, lo-fi.
- "happy": Upbeat, bouncy moves. Good for pop, dance, funk, disco.
- "intense": Powerful, sharp moves. Good for rock, EDM, hip-hop, fast beats.
- "funky": Groovy, rhythmic moves. Good for funk, R&B, soul, groove-heavy music.

Respond with ONLY a JSON object like:
{"mood": "happy", "energy_scale": 0.8, "reason": "upbeat pop with strong rhythm"}

energy_scale is 0.3 to 1.0 (how big the moves should be).
Keep "reason" under 10 words."""


class MistralBrain:
    """Periodically consults Mistral AI to classify music mood."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("MISTRAL_API_KEY", "")
        self.current_mood = "happy"
        self.current_energy_scale = 0.8
        self.current_reason = ""
        self.last_call_time = 0.0
        self.call_interval = 8.0  # seconds between API calls
        self.enabled = bool(self.api_key)
        self._lock = threading.Lock()

    def analyze(self, audio_state: dict) -> dict:
        """Maybe call Mistral to analyze the current audio state.
        Returns the current mood decision."""
        now = time.time()

        # Only call API every N seconds and if music is playing
        if (self.enabled 
            and audio_state.get("has_music", False)
            and now - self.last_call_time > self.call_interval):
            self.last_call_time = now
            # Run in background to not block dance loop
            t = threading.Thread(target=self._call_mistral, args=(audio_state,), daemon=True)
            t.start()

        with self._lock:
            return {
                "mood": self.current_mood,
                "energy_scale": self.current_energy_scale,
                "reason": self.current_reason,
                "ai_enabled": self.enabled,
            }

    def _call_mistral(self, audio_state: dict):
        """Call Mistral API in background."""
        try:
            prompt = (
                f"Current audio analysis:\n"
                f"- BPM: {audio_state.get('bpm', 120)}\n"
                f"- Energy level: {audio_state.get('energy_level', 0.5):.0%}\n"
                f"- Spectral centroid: {audio_state.get('spectral_centroid', 1000)} Hz "
                f"({'bright/treble-heavy' if audio_state.get('spectral_centroid', 1000) > 2000 else 'warm/bass-heavy' if audio_state.get('spectral_centroid', 1000) < 1000 else 'balanced'})\n"
                f"- Current estimated mood: {audio_state.get('mood', 'unknown')}\n"
                f"- Beat count so far: {audio_state.get('beat_count', 0)}\n\n"
                f"What dance mood and energy level should the robot use?"
            )

            resp = requests.post(
                MISTRAL_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "mistral-small-latest",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 100,
                },
                timeout=5,
            )

            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                # Parse JSON from response
                # Handle potential markdown wrapping
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                
                data = json.loads(content)
                
                with self._lock:
                    if data.get("mood") in ("chill", "happy", "intense", "funky"):
                        self.current_mood = data["mood"]
                    if "energy_scale" in data:
                        self.current_energy_scale = max(0.3, min(1.0, float(data["energy_scale"])))
                    self.current_reason = data.get("reason", "")
                
                print(f"  🧠 Mistral: {self.current_mood} ({self.current_energy_scale:.1f}x) - {self.current_reason}", flush=True)
            else:
                print(f"  🧠 Mistral API error: {resp.status_code}", flush=True)

        except Exception as e:
            print(f"  🧠 Mistral error: {e}", flush=True)
