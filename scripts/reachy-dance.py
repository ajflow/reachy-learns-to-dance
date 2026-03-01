#!/usr/bin/env python3
"""
Reachy Mini Dance Controller via REST API

Sends choreographed dance sequences using goto endpoints.
For the full dances library (20 moves), install on the Pi:
  pip install git+https://github.com/pollen-robotics/reachy_mini_dances_library.git

This script provides REST-API-based dances that work remotely via the tunnel.

Usage:
  python reachy-dance.py --dance groovy       # Sway and roll
  python reachy-dance.py --dance headbang     # Head banger
  python reachy-dance.py --dance celebrate    # Happy celebration
  python reachy-dance.py --dance disco        # Disco moves
  python reachy-dance.py --dance nod-along    # Rhythmic nod
  python reachy-dance.py --dance chicken      # Chicken peck
  python reachy-dance.py --dance robot        # Robot-style snaps
  python reachy-dance.py --bpm 120            # Set tempo (default: 110)
  python reachy-dance.py --duration 10        # Dance for 10 seconds (default: 8)
  python reachy-dance.py --list               # Show all dances
"""

import argparse, json, math, os, sys, time
import requests

def get_base_url():
    host = os.environ.get("REACHY_HOST", "localhost")
    port = os.environ.get("REACHY_PORT", "8000")
    return f"http://{host}:{port}/api"

def goto(head=None, antennas=None, body_yaw=None, duration=0.3):
    data = {"duration": duration}
    if head:
        data["head_pose"] = head
    if antennas is not None:
        data["antennas"] = antennas
    if body_yaw is not None:
        data["body_yaw"] = body_yaw
    try:
        requests.post(f"{get_base_url()}/move/goto", json=data, timeout=5)
    except:
        pass

def wait_beat(bpm, beats=1):
    time.sleep(60.0 / bpm * beats)

# === DANCE ROUTINES ===

def dance_groovy(bpm, duration):
    """Groovy sway and roll - flowing side to side"""
    end = time.time() + duration
    while time.time() < end:
        goto(head={"roll": 20, "pitch": 10}, antennas=[30, -10], body_yaw=15, duration=0.4)
        wait_beat(bpm, 2)
        goto(head={"roll": -20, "pitch": -5}, antennas=[-10, 30], body_yaw=-15, duration=0.4)
        wait_beat(bpm, 2)
        goto(head={"roll": 10, "yaw": 15}, antennas=[20, 20], body_yaw=0, duration=0.3)
        wait_beat(bpm, 1)
        goto(head={"roll": -10, "yaw": -15}, antennas=[-5, -5], body_yaw=0, duration=0.3)
        wait_beat(bpm, 1)

def dance_headbang(bpm, duration):
    """Headbanger - high energy head isolation"""
    end = time.time() + duration
    while time.time() < end:
        goto(head={"pitch": 25}, antennas=[40, 40], duration=0.15)
        wait_beat(bpm, 0.5)
        goto(head={"pitch": -15}, antennas=[-10, -10], duration=0.15)
        wait_beat(bpm, 0.5)

def dance_celebrate(bpm, duration):
    """Celebration dance - happy antennas + swaying"""
    end = time.time() + duration
    while time.time() < end:
        goto(head={"pitch": 15, "yaw": 20}, antennas=[45, 45], body_yaw=20, duration=0.3)
        wait_beat(bpm, 1)
        goto(head={"pitch": 5, "yaw": -20}, antennas=[-10, -10], body_yaw=-20, duration=0.3)
        wait_beat(bpm, 1)
        goto(head={"pitch": 20, "roll": 15}, antennas=[30, 45], body_yaw=10, duration=0.3)
        wait_beat(bpm, 1)
        goto(head={"pitch": 5, "roll": -15}, antennas=[45, 30], body_yaw=-10, duration=0.3)
        wait_beat(bpm, 1)

def dance_disco(bpm, duration):
    """Disco fever - body rotation + head poses"""
    end = time.time() + duration
    while time.time() < end:
        # Point right
        goto(head={"yaw": 30, "pitch": -10}, antennas=[40, 0], body_yaw=30, duration=0.4)
        wait_beat(bpm, 2)
        # Point left
        goto(head={"yaw": -30, "pitch": -10}, antennas=[0, 40], body_yaw=-30, duration=0.4)
        wait_beat(bpm, 2)
        # Look up center
        goto(head={"yaw": 0, "pitch": 20}, antennas=[35, 35], body_yaw=0, duration=0.3)
        wait_beat(bpm, 1)
        # Down
        goto(head={"yaw": 0, "pitch": -15}, antennas=[5, 5], body_yaw=0, duration=0.3)
        wait_beat(bpm, 1)

def dance_nod_along(bpm, duration):
    """Rhythmic nod - subtle groovy nod with antenna bounce"""
    end = time.time() + duration
    while time.time() < end:
        goto(head={"pitch": 15}, antennas=[25, 25], duration=0.2)
        wait_beat(bpm, 1)
        goto(head={"pitch": -5}, antennas=[5, 5], duration=0.2)
        wait_beat(bpm, 1)

def dance_chicken(bpm, duration):
    """Chicken peck - pecking head bop"""
    end = time.time() + duration
    while time.time() < end:
        # Peck forward
        goto(head={"pitch": -20, "yaw": 5}, antennas=[10, 10], duration=0.15)
        wait_beat(bpm, 0.5)
        # Pull back
        goto(head={"pitch": 10, "yaw": -5}, antennas=[25, 25], duration=0.2)
        wait_beat(bpm, 0.5)
        # Peck other side
        goto(head={"pitch": -20, "yaw": -5}, antennas=[10, 10], duration=0.15)
        wait_beat(bpm, 0.5)
        goto(head={"pitch": 10, "yaw": 5}, antennas=[25, 25], duration=0.2)
        wait_beat(bpm, 0.5)

def dance_robot(bpm, duration):
    """Robot style - sharp snappy moves with pauses"""
    end = time.time() + duration
    while time.time() < end:
        goto(head={"yaw": 25, "pitch": 0, "roll": 0}, antennas=[0, 40], body_yaw=25, duration=0.15)
        wait_beat(bpm, 1.5)
        goto(head={"yaw": -25, "pitch": 15, "roll": 0}, antennas=[40, 0], body_yaw=-25, duration=0.15)
        wait_beat(bpm, 1.5)
        goto(head={"yaw": 0, "pitch": -10, "roll": 20}, antennas=[20, 20], body_yaw=0, duration=0.15)
        wait_beat(bpm, 1)
        goto(head={"yaw": 0, "pitch": 0, "roll": -20}, antennas=[35, 35], body_yaw=0, duration=0.15)
        wait_beat(bpm, 1)

DANCES = {
    "groovy": ("Groovy Sway & Roll", dance_groovy),
    "headbang": ("Headbanger Combo", dance_headbang),
    "celebrate": ("Happy Celebration", dance_celebrate),
    "disco": ("Disco Fever", dance_disco),
    "nod-along": ("Rhythmic Nod", dance_nod_along),
    "chicken": ("Chicken Peck", dance_chicken),
    "robot": ("Robot Snaps", dance_robot),
}

def dance_choreo(choreo_path):
    """Play a choreography JSON file (from tiktok-to-dance.py)"""
    with open(choreo_path) as f:
        data = json.load(f)

    keyframes = data["keyframes"]
    title = data.get("title", "Unknown")
    print(f"🎬 Playing choreography: {title} ({len(keyframes)} keyframes, {data.get('duration', 0):.1f}s)")

    start = time.time()
    for i, kf in enumerate(keyframes):
        # Wait until keyframe time
        target_time = start + kf["t"]
        now = time.time()
        if target_time > now:
            time.sleep(target_time - now)

        # Calculate duration to next keyframe
        if i + 1 < len(keyframes):
            dur = keyframes[i + 1]["t"] - kf["t"]
        else:
            dur = 0.2
        dur = max(0.1, min(dur, 0.5))

        goto(
            head=kf.get("head"),
            antennas=kf.get("antennas"),
            body_yaw=kf.get("body_yaw"),
            duration=dur,
        )


def main():
    parser = argparse.ArgumentParser(description="Reachy Mini Dance Controller")
    parser.add_argument("--dance", choices=list(DANCES.keys()), help="Dance to perform")
    parser.add_argument("--choreo", help="Play choreography JSON (from tiktok-to-dance.py)")
    parser.add_argument("--bpm", type=int, default=110, help="Tempo in BPM (default: 110)")
    parser.add_argument("--duration", type=float, default=8, help="Duration in seconds (default: 8)")
    parser.add_argument("--list", action="store_true", help="List all dances")
    args = parser.parse_args()

    if args.list:
        print("🕺 Available dances:")
        for key, (name, _) in DANCES.items():
            print(f"   {key:15s} {name}")
        return

    if args.choreo:
        try:
            dance_choreo(args.choreo)
        except KeyboardInterrupt:
            pass
        goto(head={"yaw": 0, "pitch": 0, "roll": 0}, antennas=[0, 0], body_yaw=0, duration=0.5)
        print("✅ Choreography complete!")
        return

    if not args.dance:
        parser.print_help()
        return

    name, fn = DANCES[args.dance]
    print(f"🕺 Dancing: {name} @ {args.bpm} BPM for {args.duration}s")

    try:
        fn(args.bpm, args.duration)
    except KeyboardInterrupt:
        pass

    # Return to neutral
    goto(head={"yaw": 0, "pitch": 0, "roll": 0}, antennas=[0, 0], body_yaw=0, duration=0.5)
    print("✅ Dance complete!")

if __name__ == "__main__":
    main()
