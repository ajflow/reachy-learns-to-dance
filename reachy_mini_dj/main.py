"""Reachy Mini DJ: AI-choreographed dancing robot.

Listens to live music, analyzes audio in real-time, and uses
Mistral AI as a dance choreographer via function calling.
The AI actively decides moves, mood, energy, and timing.
"""

import json
import random
import threading
import time

import numpy as np
from reachy_mini import ReachyMini, ReachyMiniApp, utils
from reachy_mini_dances_library.collection.dance import AVAILABLE_MOVES

from .audio_engine import AudioEngine
from .mistral_brain import MistralBrain

# Fallback mood pools (used when AI hasn't queued a specific move)
MOOD_MOVES = {
    "chill": ["simple_nod", "head_tilt_roll", "side_to_side_sway", "chin_lead", "pendulum_swing"],
    "happy": ["yeah_nod", "uh_huh_tilt", "chicken_peck", "side_peekaboo", "groovy_sway_and_roll", "side_to_side_sway"],
    "intense": ["jackson_square", "polyrhythm_combo", "interwoven_spirals", "grid_snap", "neck_recoil", "sharp_side_tilt"],
    "funky": ["groovy_sway_and_roll", "side_glance_flick", "stumble_and_recover", "sharp_side_tilt", "dizzy_spin"],
}

NEUTRAL_POS = np.array([0.0, 0.0, 0.0])
NEUTRAL_EUL = np.zeros(3)

# Shared state for dashboard
_state = {}
_state_lock = threading.Lock()


def get_state():
    with _state_lock:
        return dict(_state)


def set_state(**kwargs):
    with _state_lock:
        _state.update(kwargs)


class ReachyMiniDJ(ReachyMiniApp):
    """AI-choreographed dancing robot powered by Mistral."""

    custom_app_url: str | None = "http://localhost:8001"

    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event):
        # Audio engine handles all music analysis
        audio = AudioEngine(device=2)
        audio.start()

        # Mistral AI choreographer (function calling)
        mistral = MistralBrain()

        # Web dashboard
        web_thread = threading.Thread(target=self._run_web_server, daemon=True)
        web_thread.start()

        # Dance state
        current_move_name = "simple_nod"
        move_fn, move_params, move_meta = AVAILABLE_MOVES[current_move_name]
        t_beats = 0.0
        sequence_beat_counter = 0.0
        beats_per_sequence = 8
        dancing = False
        silence_timer = 0.0
        move_history = []
        amplitude_scale = 0.8

        set_state(
            is_dancing=False,
            current_move="none",
            move_history=[],
            ai_log=[],
        )

        control_ts = 0.01  # 100Hz
        last_loop_time = time.time()

        try:
            while not stop_event.is_set():
                now = time.time()
                dt = now - last_loop_time
                last_loop_time = now

                # Get audio state
                audio_state = audio.get_state()

                if audio.has_music:
                    silence_timer = 0.0

                    if not dancing:
                        dancing = True
                        t_beats = 0.0
                        sequence_beat_counter = 0.0
                        current_move_name, move_fn, move_params = self._pick_move(
                            "happy", current_move_name
                        )
                        move_history = [current_move_name]

                    # Consult Mistral AI choreographer
                    ai_state = mistral.analyze(audio_state)
                    mood = ai_state["mood"]

                    # Check if AI queued a specific move
                    queued = ai_state.get("queued_move")
                    if queued and queued in AVAILABLE_MOVES:
                        current_move_name = queued
                        move_fn, move_params, move_meta = AVAILABLE_MOVES[queued]
                        sequence_beat_counter = 0.0
                        move_history.append(current_move_name)
                        if len(move_history) > 20:
                            move_history.pop(0)

                    # Use AI's beats_per_sequence if set
                    ai_bps = ai_state.get("beats_per_sequence")
                    if ai_bps:
                        beats_per_sequence = ai_bps

                    # Scale amplitude with energy + AI direction
                    amplitude_scale = min(1.0, 0.4 + audio.energy_level * 0.6) * ai_state["energy_scale"]

                    # Advance beat counter using detected BPM
                    bpm = audio.bpm
                    beats_this_frame = dt * (bpm / 60.0)
                    t_beats += beats_this_frame
                    sequence_beat_counter += beats_this_frame

                    # Switch move every N beats (if AI hasn't already queued one)
                    if sequence_beat_counter >= beats_per_sequence:
                        sequence_beat_counter = 0.0
                        current_move_name, move_fn, move_params = self._pick_move(
                            mood, current_move_name
                        )
                        move_history.append(current_move_name)
                        if len(move_history) > 20:
                            move_history.pop(0)

                    # Scale amplitude params
                    current_params = move_params.copy()
                    for key in current_params:
                        if "amplitude" in key or "_amp" in key:
                            current_params[key] *= amplitude_scale

                    # Get movement offsets
                    offsets = move_fn(t_beats, **current_params)

                    # Apply to robot
                    final_pos = NEUTRAL_POS + offsets.position_offset
                    final_eul = NEUTRAL_EUL + offsets.orientation_offset
                    final_ant = offsets.antennas_offset

                    reachy_mini.set_target(
                        utils.create_head_pose(*final_pos, *final_eul, degrees=False),
                        antennas=final_ant,
                    )

                    # Update dashboard state
                    set_state(
                        is_dancing=True,
                        current_move=current_move_name,
                        move_history=list(move_history),
                        amplitude=round(amplitude_scale, 2),
                        ai_mood=ai_state["mood"],
                        ai_reason=ai_state["reason"],
                        ai_enabled=ai_state["ai_enabled"],
                        ai_log=ai_state.get("ai_log", []),
                        ai_call_count=ai_state.get("call_count", 0),
                        beats_per_sequence=beats_per_sequence,
                        **audio_state,
                    )

                else:
                    silence_timer += dt
                    if dancing and silence_timer > 2.0:
                        dancing = False
                        set_state(
                            is_dancing=False,
                            current_move="none",
                            ai_log=mistral.ai_log if hasattr(mistral, 'ai_log') else [],
                            **audio_state,
                        )
                    else:
                        set_state(**audio_state)

                time.sleep(control_ts)

        finally:
            audio.stop()

    def _pick_move(self, mood, current_name):
        """Pick a new move appropriate for the mood (fallback when AI hasn't queued one)."""
        pool = MOOD_MOVES.get(mood, MOOD_MOVES["happy"])
        candidates = [m for m in pool if m != current_name and m in AVAILABLE_MOVES]
        if not candidates:
            candidates = [m for m in pool if m in AVAILABLE_MOVES]
        name = random.choice(candidates)
        fn, params, meta = AVAILABLE_MOVES[name]
        return name, fn, params

    def _run_web_server(self):
        """HTTP server for the dashboard."""
        import http.server
        import os
        import socket

        static_dir = os.path.join(os.path.dirname(__file__), "static")

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=static_dir, **kwargs)

            def do_GET(self):
                if self.path == "/api/state":
                    state = get_state()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps(state).encode())
                else:
                    super().do_GET()

            def log_message(self, format, *args):
                pass

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", 8001))
        sock.listen(5)
        server = http.server.HTTPServer(("0.0.0.0", 8001), Handler, bind_and_activate=False)
        server.socket = sock
        print("Dashboard running on 0.0.0.0:8001", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    app = ReachyMiniDJ()
    try:
        app.wrapped_run()
    except KeyboardInterrupt:
        app.stop()
