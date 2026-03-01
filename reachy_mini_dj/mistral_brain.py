"""Mistral AI Dance Choreographer Agent.

Uses function calling to actively choreograph the robot rather than
just classifying mood. Maintains a rolling conversation so the AI
builds context about the music session over time.
"""

import json
import os
import threading
import time
from typing import Optional

import requests

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "set_dance_mood",
            "description": "Set the robot's overall dance style/mood. Call this when the music character changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mood": {
                        "type": "string",
                        "enum": ["chill", "happy", "intense", "funky"],
                        "description": "chill=gentle/slow, happy=bouncy/upbeat, intense=sharp/powerful, funky=groovy/rhythmic"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief reason for this choice (shown on dashboard)"
                    }
                },
                "required": ["mood", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_energy",
            "description": "Set how big the dance movements are. Higher = more dramatic movements.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scale": {
                        "type": "number",
                        "description": "Movement amplitude from 0.3 (subtle) to 1.0 (full range)"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief reason"
                    }
                },
                "required": ["scale"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "queue_move",
            "description": "Queue a specific dance move to play next. Use this to pick the perfect move for what you hear.",
            "parameters": {
                "type": "object",
                "properties": {
                    "move_name": {
                        "type": "string",
                        "enum": [
                            "simple_nod", "head_tilt_roll", "side_to_side_sway",
                            "dizzy_spin", "stumble_and_recover", "headbanger_combo",
                            "interwoven_spirals", "sharp_side_tilt", "side_peekaboo",
                            "yeah_nod", "uh_huh_tilt", "neck_recoil", "chin_lead",
                            "groovy_sway_and_roll", "chicken_peck", "side_glance_flick",
                            "polyrhythm_combo", "grid_snap", "pendulum_swing",
                            "jackson_square"
                        ],
                        "description": "Name of the dance move"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why this move fits right now"
                    }
                },
                "required": ["move_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_sequence_length",
            "description": "Set how many beats before switching to a new move. Shorter = more variety, longer = more groove.",
            "parameters": {
                "type": "object",
                "properties": {
                    "beats": {
                        "type": "integer",
                        "description": "Beats per move sequence (4=rapid changes, 8=normal, 16=extended groove, 32=long commitment)"
                    }
                },
                "required": ["beats"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are the AI brain of a dancing robot called Reachy Mini DJ. You are a dance choreographer who listens to music through audio analysis data and actively directs the robot's performance.

You receive updates about what the robot's microphone hears: BPM, energy level, spectral features, and beat count. Your job is to use your tools to choreograph the dance in real-time.

IMPORTANT RULES:
- Always call at least one tool. You are a choreographer, not a commentator.
- When the music character changes (tempo shift, energy change, genre shift), call set_dance_mood.
- Match energy scale to the music intensity. Quiet = 0.3-0.5, medium = 0.5-0.7, loud = 0.7-1.0.
- Pick specific moves that match the vibe. Don't just set mood, queue actual moves.
- Vary your choices. Don't repeat the same move twice in a row.
- Keep reasons short (under 15 words) since they show on the dashboard.

MOVE GUIDE:
- Chill: simple_nod (gentle), head_tilt_roll (smooth), pendulum_swing (hypnotic), chin_lead (subtle)
- Happy: yeah_nod (bouncy), chicken_peck (playful), side_peekaboo (fun), uh_huh_tilt (groovy)
- Intense: jackson_square (sharp), headbanger_combo (powerful), grid_snap (precise), neck_recoil (punchy)
- Funky: groovy_sway_and_roll (smooth), side_glance_flick (sassy), stumble_and_recover (dramatic), dizzy_spin (wild)

You have personality. Get excited when the music gets intense. Be chill when it's mellow. React to changes."""


class MistralBrain:
    """AI dance choreographer using Mistral function calling."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("MISTRAL_API_KEY", "")
        self.enabled = bool(self.api_key)

        # Current choreography state
        self.current_mood = "happy"
        self.current_energy_scale = 0.8
        self.current_reason = ""
        self.queued_move = None  # Next move the AI wants
        self.beats_per_sequence = 8

        # Conversation history for context
        self.conversation = []
        self.max_history = 12  # Keep last N exchanges to manage tokens

        # AI log for dashboard
        self.ai_log = []  # List of {time, role, content} for dashboard display
        self.max_log = 30

        # Timing
        self.last_call_time = 0.0
        self.call_interval = 8.0  # seconds between choreography updates
        self.call_count = 0

        self._lock = threading.Lock()

    def analyze(self, audio_state: dict) -> dict:
        """Consult the AI choreographer. Returns current dance directives."""
        now = time.time()

        if (self.enabled
            and audio_state.get("has_music", False)
            and now - self.last_call_time > self.call_interval):
            self.last_call_time = now
            t = threading.Thread(target=self._choreograph, args=(audio_state,), daemon=True)
            t.start()

        with self._lock:
            result = {
                "mood": self.current_mood,
                "energy_scale": self.current_energy_scale,
                "reason": self.current_reason,
                "ai_enabled": self.enabled,
                "queued_move": self.queued_move,
                "beats_per_sequence": self.beats_per_sequence,
                "ai_log": list(self.ai_log),
                "call_count": self.call_count,
            }
            # Clear queued move after it's been read
            self.queued_move = None
            return result

    def _choreograph(self, audio_state: dict):
        """Call Mistral with function calling to get choreography decisions."""
        try:
            # Build the audio report
            bpm = audio_state.get("bpm", 120)
            energy = audio_state.get("energy_level", 0.5)
            centroid = audio_state.get("spectral_centroid", 1000)
            beat_count = audio_state.get("beat_count", 0)
            volume = audio_state.get("volume", 0)
            mood_est = audio_state.get("mood", "unknown")

            # Describe the audio character
            brightness = "bright/treble-heavy" if centroid > 2000 else "warm/bass-heavy" if centroid < 1000 else "balanced"
            energy_desc = "very quiet" if energy < 0.2 else "low energy" if energy < 0.4 else "moderate" if energy < 0.6 else "high energy" if energy < 0.8 else "maximum energy"

            user_msg = (
                f"Music update (beat #{beat_count}):\n"
                f"- BPM: {bpm} | Energy: {energy:.0%} ({energy_desc}) | Volume: {volume:.4f}\n"
                f"- Spectral character: {centroid:.0f}Hz ({brightness})\n"
                f"- Audio mood estimate: {mood_est}\n"
                f"- Currently dancing: mood={self.current_mood}, energy_scale={self.current_energy_scale:.1f}"
            )

            # Add to conversation
            self.conversation.append({"role": "user", "content": user_msg})

            # Trim history
            if len(self.conversation) > self.max_history:
                self.conversation = self.conversation[-self.max_history:]

            # Build messages
            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.conversation

            resp = requests.post(
                MISTRAL_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "mistral-small-latest",
                    "messages": messages,
                    "tools": TOOLS,
                    "tool_choice": "any",
                    "temperature": 0.4,
                    "max_tokens": 300,
                },
                timeout=8,
            )

            if resp.status_code != 200:
                print(f"  Mistral API error: {resp.status_code}", flush=True)
                self._add_log("system", f"API error: {resp.status_code}")
                return

            data = resp.json()
            choice = data["choices"][0]
            msg = choice["message"]

            # Log any text content
            if msg.get("content"):
                self._add_log("ai", msg["content"])
                self.conversation.append({"role": "assistant", "content": msg["content"]})

            # Process tool calls
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                # Add assistant message with tool calls to conversation
                self.conversation.append({
                    "role": "assistant",
                    "content": msg.get("content", ""),
                    "tool_calls": tool_calls
                })

                tool_results = []
                for tc in tool_calls:
                    fn_name = tc["function"]["name"]
                    fn_args = json.loads(tc["function"]["arguments"])
                    result = self._execute_tool(fn_name, fn_args)
                    tool_results.append({
                        "role": "tool",
                        "name": fn_name,
                        "content": json.dumps(result),
                        "tool_call_id": tc["id"]
                    })

                # Add tool results to conversation
                self.conversation.extend(tool_results)

            with self._lock:
                self.call_count += 1

            print(f"  Mistral choreography #{self.call_count}: {len(tool_calls)} tool calls", flush=True)

        except Exception as e:
            print(f"  Mistral error: {e}", flush=True)
            self._add_log("system", f"Error: {str(e)[:50]}")

    def _execute_tool(self, name: str, args: dict) -> dict:
        """Execute a choreography tool call."""
        with self._lock:
            if name == "set_dance_mood":
                mood = args.get("mood", self.current_mood)
                reason = args.get("reason", "")
                self.current_mood = mood
                self.current_reason = reason
                self._add_log("tool", f"Mood > {mood}: {reason}")
                print(f"    set_dance_mood({mood}): {reason}", flush=True)
                return {"status": "ok", "mood": mood}

            elif name == "set_energy":
                scale = max(0.3, min(1.0, float(args.get("scale", 0.8))))
                reason = args.get("reason", "")
                self.current_energy_scale = scale
                if reason:
                    self._add_log("tool", f"Energy > {scale:.0%}: {reason}")
                else:
                    self._add_log("tool", f"Energy > {scale:.0%}")
                print(f"    set_energy({scale:.1f}): {reason}", flush=True)
                return {"status": "ok", "energy_scale": scale}

            elif name == "queue_move":
                move = args.get("move_name", "")
                reason = args.get("reason", "")
                self.queued_move = move
                self._add_log("tool", f"Move > {move}: {reason}")
                print(f"    queue_move({move}): {reason}", flush=True)
                return {"status": "ok", "queued_move": move}

            elif name == "set_sequence_length":
                beats = max(4, min(32, int(args.get("beats", 8))))
                self.beats_per_sequence = beats
                self._add_log("tool", f"Sequence > {beats} beats")
                print(f"    set_sequence_length({beats})", flush=True)
                return {"status": "ok", "beats": beats}

            else:
                return {"status": "error", "message": f"Unknown tool: {name}"}

    def _add_log(self, role: str, content: str):
        """Add entry to AI log for dashboard display."""
        self.ai_log.append({
            "time": time.time(),
            "role": role,
            "content": content
        })
        if len(self.ai_log) > self.max_log:
            self.ai_log.pop(0)
