#!/usr/bin/env python3
"""
Reachy Mini Remote Control via REST API

Controls a Reachy Mini (Wireless) over the network.
Requires the robot's IP or hostname (default: reachy-mini.local).

Usage:
  python reachy-control.py --action wake_up
  python reachy-control.py --action sleep
  python reachy-control.py --action state
  python reachy-control.py --action move --head-yaw 30 --head-pitch 10 --duration 1.5
  python reachy-control.py --action antennas --left 45 --right 45
  python reachy-control.py --action body --yaw 30 --duration 1.5
  python reachy-control.py --action emotion --name happy
  python reachy-control.py --action say --text "Hello world"
  python reachy-control.py --action nod
  python reachy-control.py --action shake
  python reachy-control.py --action look --x 0 --y 0 --z 30

Environment:
  REACHY_HOST - Robot hostname/IP (default: reachy-mini.local)
  REACHY_PORT - API port (default: 8000)
"""

import argparse, json, os, sys, time
import requests

def get_base_url():
    host = os.environ.get("REACHY_HOST", "reachy-mini.local")
    port = os.environ.get("REACHY_PORT", "8000")
    return f"http://{host}:{port}/api"

def api(method, path, data=None, timeout=10):
    url = f"{get_base_url()}{path}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=timeout)
        else:
            r = requests.post(url, json=data, timeout=timeout)
        r.raise_for_status()
        try:
            return r.json()
        except:
            return {"status": "ok"}
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Cannot reach Reachy Mini at {url}", file=sys.stderr)
        print("Check: robot powered on, connected to same WiFi, hostname/IP correct", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print(f"Response: {r.text[:500]}", file=sys.stderr)
        sys.exit(1)

def cmd_state(args):
    state = api("GET", "/state/full")
    print(json.dumps(state, indent=2))

def cmd_wake_up(args):
    result = api("POST", "/move/play/wake_up")
    print("✅ Reachy Mini is awake!")
    return result

def cmd_sleep(args):
    result = api("POST", "/move/play/goto_sleep")
    print("😴 Reachy Mini is sleeping")
    return result

def cmd_move(args):
    data = {"duration": args.duration or 1.0}
    head = {}
    if args.head_yaw is not None:
        head["yaw"] = args.head_yaw
    if args.head_pitch is not None:
        head["pitch"] = args.head_pitch
    if args.head_roll is not None:
        head["roll"] = args.head_roll
    if head:
        data["head_pose"] = head
    if args.body_yaw is not None:
        data["body_yaw"] = args.body_yaw
    result = api("POST", "/move/goto", data)
    print(f"✅ Moved: {json.dumps(data)}")
    return result

def cmd_antennas(args):
    left = args.left if args.left is not None else 0
    right = args.right if args.right is not None else 0
    data = {
        "antennas": [left, right],
        "duration": args.duration or 0.5,
    }
    result = api("POST", "/move/goto", data)
    print(f"✅ Antennas: left={left}°, right={right}°")
    return result

def cmd_body(args):
    data = {
        "body_yaw": args.yaw or 0,
        "duration": args.duration or 1.0,
    }
    result = api("POST", "/move/goto", data)
    print(f"✅ Body rotated to {args.yaw}°")
    return result

def cmd_emotion(args):
    result = api("POST", f"/move/play/recorded-move-dataset/pollen-robotics/reachy-mini-emotions-library/{args.name}")
    print(f"✅ Playing emotion: {args.name}")
    return result

def cmd_nod(args):
    """Nod yes - quick head pitch sequence"""
    for _ in range(3):
        api("POST", "/move/goto", {"head_pose": {"pitch": 15}, "duration": 0.2})
        time.sleep(0.25)
        api("POST", "/move/goto", {"head_pose": {"pitch": -5}, "duration": 0.2})
        time.sleep(0.25)
    api("POST", "/move/goto", {"head_pose": {"pitch": 0}, "duration": 0.3})
    print("✅ Nodded yes")

def cmd_shake(args):
    """Shake head no - quick head yaw sequence"""
    for _ in range(3):
        api("POST", "/move/goto", {"head_pose": {"yaw": 20}, "duration": 0.2})
        time.sleep(0.25)
        api("POST", "/move/goto", {"head_pose": {"yaw": -20}, "duration": 0.2})
        time.sleep(0.25)
    api("POST", "/move/goto", {"head_pose": {"yaw": 0}, "duration": 0.3})
    print("✅ Shook head no")

def cmd_look(args):
    data = {
        "head_pose": {"yaw": args.x or 0, "pitch": args.y or 0, "roll": args.z or 0},
        "duration": args.duration or 1.0,
    }
    result = api("POST", "/move/goto", data)
    print(f"✅ Looking at ({args.x}, {args.y}, {args.z})")
    return result

def cmd_motors(args):
    mode = args.mode or "enabled"
    result = api("POST", f"/motors/set_mode/{mode}")
    print(f"✅ Motors: {mode}")
    return result

def cmd_stop(args):
    result = api("POST", "/move/stop")
    print("⛔ All moves stopped")
    return result

def main():
    parser = argparse.ArgumentParser(description="Reachy Mini Remote Control")
    parser.add_argument("--action", required=True,
        choices=["state", "wake_up", "sleep", "move", "antennas", "body",
                 "emotion", "nod", "shake", "look", "motors", "stop"])
    parser.add_argument("--head-yaw", type=float)
    parser.add_argument("--head-pitch", type=float)
    parser.add_argument("--head-roll", type=float)
    parser.add_argument("--body-yaw", type=float)
    parser.add_argument("--yaw", type=float)
    parser.add_argument("--left", type=float, help="Left antenna angle (degrees)")
    parser.add_argument("--right", type=float, help="Right antenna angle (degrees)")
    parser.add_argument("--duration", type=float)
    parser.add_argument("--name", help="Emotion name (happy, sad, etc.)")
    parser.add_argument("--text", help="Text for say action")
    parser.add_argument("--mode", help="Motor mode: enabled, disabled, gravity_compensation")
    parser.add_argument("--x", type=float, default=0)
    parser.add_argument("--y", type=float, default=0)
    parser.add_argument("--z", type=float, default=0)

    args = parser.parse_args()

    actions = {
        "state": cmd_state,
        "wake_up": cmd_wake_up,
        "sleep": cmd_sleep,
        "move": cmd_move,
        "antennas": cmd_antennas,
        "body": cmd_body,
        "emotion": cmd_emotion,
        "nod": cmd_nod,
        "shake": cmd_shake,
        "look": cmd_look,
        "motors": cmd_motors,
        "stop": cmd_stop,
    }

    actions[args.action](args)

if __name__ == "__main__":
    main()
