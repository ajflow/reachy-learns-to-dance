#!/usr/bin/env python3
"""
TikTok Video → Reachy Mini Dance Choreography

Downloads a TikTok video, extracts human pose with MediaPipe,
maps body motion to Reachy Mini joints, and outputs a choreography JSON.

Usage:
  python tiktok-to-dance.py --url "https://www.tiktok.com/@user/video/123"
  python tiktok-to-dance.py --url "..." --output dance.json --preview
  python tiktok-to-dance.py --file local_video.mp4
  python tiktok-to-dance.py --file video.mp4 --amplify 1.5   # Exaggerate moves
  python tiktok-to-dance.py --file video.mp4 --fps 10        # Sample rate

Then play it:
  python reachy-dance.py --choreo dance.json
"""

import argparse, json, math, os, sys, tempfile
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
import requests

# Landmark indices (MediaPipe Pose)
LM_NOSE = 0
LM_LEFT_EAR = 7
LM_RIGHT_EAR = 8
LM_LEFT_SHOULDER = 11
LM_RIGHT_SHOULDER = 12
LM_LEFT_ELBOW = 13
LM_RIGHT_ELBOW = 14
LM_LEFT_WRIST = 15
LM_RIGHT_WRIST = 16
LM_LEFT_HIP = 23
LM_RIGHT_HIP = 24

# Path to model (bundled with skill)
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pose_landmarker.task")


def download_tiktok(url):
    """Download TikTok video via tikwm.com API or yt-dlp"""
    print(f"📥 Downloading TikTok: {url}")

    # Try tikwm first
    try:
        r = requests.post("https://www.tikwm.com/api/", data={"url": url}, timeout=30)
        data = r.json()
        if data.get("code") == 0:
            video_url = data["data"]["play"]
            tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            vr = requests.get(video_url, timeout=60)
            tmp.write(vr.content)
            tmp.close()
            title = data["data"].get("title", "")
            print(f"   Downloaded via tikwm ({len(vr.content) // 1024}KB)")
            return tmp.name, title, {}
    except Exception as e:
        print(f"   tikwm failed: {e}")

    # Fallback: yt-dlp
    try:
        import subprocess
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tmp.close()
        result = subprocess.run(
            ["yt-dlp", "-o", tmp.name, "--force-overwrite", url],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and os.path.getsize(tmp.name) > 0:
            print(f"   Downloaded via yt-dlp")
            return tmp.name, "", {}
    except Exception as e:
        print(f"   yt-dlp failed: {e}")

    print("ERROR: Could not download video. Provide a local file with --file", file=sys.stderr)
    sys.exit(1)


def extract_poses(video_path, sample_fps=10):
    """Extract pose landmarks from video frames using MediaPipe Tasks API"""
    print(f"🔍 Extracting poses from video (sample rate: {sample_fps} fps)...")

    if not os.path.exists(MODEL_PATH):
        print(f"   Downloading pose model...")
        r = requests.get(
            "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task",
            timeout=60
        )
        with open(MODEL_PATH, "wb") as f:
            f.write(r.content)

    base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
    options = mp_vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=mp_vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    landmarker = mp_vision.PoseLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(video_path)
    video_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / video_fps

    frame_interval = max(1, int(video_fps / sample_fps))
    frames_data = []
    frame_idx = 0
    processed = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = int(frame_idx * 1000 / video_fps)

            results = landmarker.detect_for_video(mp_image, timestamp_ms)

            if results.pose_landmarks and len(results.pose_landmarks) > 0:
                lm = results.pose_landmarks[0]
                timestamp = frame_idx / video_fps
                frames_data.append({
                    "t": round(timestamp, 3),
                    "landmarks": extract_key_landmarks(lm),
                })
                processed += 1

        frame_idx += 1

    cap.release()
    landmarker.close()

    print(f"   Processed {processed} frames over {duration:.1f}s")
    return frames_data, video_fps, duration


def extract_key_landmarks(landmarks):
    """Extract the landmarks we care about for Reachy mapping"""
    def lm(idx):
        l = landmarks[idx]
        return {"x": l.x, "y": l.y, "z": l.z, "v": l.visibility}

    return {
        "nose": lm(LM_NOSE),
        "left_ear": lm(LM_LEFT_EAR),
        "right_ear": lm(LM_RIGHT_EAR),
        "left_shoulder": lm(LM_LEFT_SHOULDER),
        "right_shoulder": lm(LM_RIGHT_SHOULDER),
        "left_elbow": lm(LM_LEFT_ELBOW),
        "right_elbow": lm(LM_RIGHT_ELBOW),
        "left_wrist": lm(LM_LEFT_WRIST),
        "right_wrist": lm(LM_RIGHT_WRIST),
        "left_hip": lm(LM_LEFT_HIP),
        "right_hip": lm(LM_RIGHT_HIP),
    }


def map_to_reachy(frames_data, amplify=1.0):
    """Map human pose landmarks to Reachy Mini joint commands"""
    print(f"🤖 Mapping poses to Reachy joints (amplify: {amplify}x)...")

    choreography = []

    for i, frame in enumerate(frames_data):
        lm = frame["landmarks"]
        t = frame["t"]

        # --- HEAD YAW (left/right turn) ---
        # Derived from nose position relative to ear midpoint
        nose_x = lm["nose"]["x"]
        ear_mid_x = (lm["left_ear"]["x"] + lm["right_ear"]["x"]) / 2
        head_yaw = (nose_x - ear_mid_x) * -300 * amplify  # Negative = look right
        head_yaw = clamp(head_yaw, -40, 40)

        # --- HEAD PITCH (up/down nod) ---
        # Derived from nose Y relative to shoulder midpoint Y
        nose_y = lm["nose"]["y"]
        shoulder_mid_y = (lm["left_shoulder"]["y"] + lm["right_shoulder"]["y"]) / 2
        head_pitch = (shoulder_mid_y - nose_y - 0.25) * 200 * amplify
        head_pitch = clamp(head_pitch, -35, 35)

        # --- HEAD ROLL (side tilt) ---
        # Derived from ear height difference
        left_ear_y = lm["left_ear"]["y"]
        right_ear_y = lm["right_ear"]["y"]
        head_roll = (left_ear_y - right_ear_y) * 200 * amplify
        head_roll = clamp(head_roll, -35, 35)

        # --- BODY YAW (torso rotation) ---
        # Derived from shoulder depth difference (z-axis)
        left_shoulder_z = lm["left_shoulder"]["z"]
        right_shoulder_z = lm["right_shoulder"]["z"]
        body_yaw = (left_shoulder_z - right_shoulder_z) * 400 * amplify
        body_yaw = clamp(body_yaw, -60, 60)

        # --- ANTENNAS (mapped from arm raise) ---
        # Left antenna = left arm raise (wrist Y relative to shoulder Y)
        left_arm = (lm["left_shoulder"]["y"] - lm["left_wrist"]["y"]) * 150 * amplify
        left_antenna = clamp(left_arm, -20, 45)

        right_arm = (lm["right_shoulder"]["y"] - lm["right_wrist"]["y"]) * 150 * amplify
        right_antenna = clamp(right_arm, -20, 45)

        choreography.append({
            "t": t,
            "head": {
                "yaw": round(head_yaw, 1),
                "pitch": round(head_pitch, 1),
                "roll": round(head_roll, 1),
            },
            "body_yaw": round(body_yaw, 1),
            "antennas": [round(left_antenna, 1), round(right_antenna, 1)],
        })

    # Smooth the output to reduce jitter
    choreography = smooth_choreography(choreography)
    return choreography


def smooth_choreography(choreo, window=3):
    """Simple moving average to smooth jittery pose data"""
    if len(choreo) < window:
        return choreo

    smoothed = []
    for i in range(len(choreo)):
        start = max(0, i - window // 2)
        end = min(len(choreo), i + window // 2 + 1)
        chunk = choreo[start:end]

        avg_head = {
            k: round(sum(c["head"][k] for c in chunk) / len(chunk), 1)
            for k in ["yaw", "pitch", "roll"]
        }
        avg_body = round(sum(c["body_yaw"] for c in chunk) / len(chunk), 1)
        avg_ant = [
            round(sum(c["antennas"][0] for c in chunk) / len(chunk), 1),
            round(sum(c["antennas"][1] for c in chunk) / len(chunk), 1),
        ]

        smoothed.append({
            "t": choreo[i]["t"],
            "head": avg_head,
            "body_yaw": avg_body,
            "antennas": avg_ant,
        })

    return smoothed


def clamp(val, lo, hi):
    return max(lo, min(hi, val))


def estimate_bpm(choreography):
    """Rough BPM estimate from head pitch oscillation frequency"""
    if len(choreography) < 10:
        return 110  # default

    pitches = [c["head"]["pitch"] for c in choreography]
    times = [c["t"] for c in choreography]

    # Count zero-crossings of pitch
    mean_p = sum(pitches) / len(pitches)
    crossings = 0
    for i in range(1, len(pitches)):
        if (pitches[i-1] - mean_p) * (pitches[i] - mean_p) < 0:
            crossings += 1

    duration = times[-1] - times[0]
    if duration <= 0:
        return 110

    # Each full oscillation = 2 crossings = 1 beat (roughly)
    beats = crossings / 2
    bpm = (beats / duration) * 60
    return max(60, min(200, round(bpm)))


def preview_choreography(choreo):
    """Print a text visualization of the choreography"""
    print(f"\n📊 Choreography Preview ({len(choreo)} keyframes):")
    print(f"{'Time':>6s} {'Yaw':>6s} {'Pitch':>6s} {'Roll':>6s} {'Body':>6s} {'L.Ant':>6s} {'R.Ant':>6s}")
    print("-" * 45)
    # Show every Nth frame
    step = max(1, len(choreo) // 20)
    for i in range(0, len(choreo), step):
        c = choreo[i]
        print(f"{c['t']:6.2f} {c['head']['yaw']:6.1f} {c['head']['pitch']:6.1f} "
              f"{c['head']['roll']:6.1f} {c['body_yaw']:6.1f} {c['antennas'][0]:6.1f} {c['antennas'][1]:6.1f}")


def save_choreography(choreo, output_path, title="", bpm=110):
    """Save choreography as JSON"""
    data = {
        "title": title,
        "bpm": bpm,
        "keyframes": choreo,
        "duration": choreo[-1]["t"] if choreo else 0,
    }
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"💾 Saved choreography to {output_path} ({len(choreo)} keyframes)")


def main():
    parser = argparse.ArgumentParser(description="TikTok Video → Reachy Mini Dance")
    parser.add_argument("--url", help="TikTok video URL")
    parser.add_argument("--file", help="Local video file path")
    parser.add_argument("--output", default="dance_choreo.json", help="Output choreography JSON")
    parser.add_argument("--fps", type=int, default=10, help="Pose sampling rate (default: 10)")
    parser.add_argument("--amplify", type=float, default=1.2, help="Motion amplification (default: 1.2)")
    parser.add_argument("--preview", action="store_true", help="Show text preview")
    args = parser.parse_args()

    if not args.url and not args.file:
        parser.print_help()
        sys.exit(1)

    # Get video
    title = ""
    if args.url:
        video_path, title, _ = download_tiktok(args.url)
    else:
        video_path = args.file
        title = os.path.splitext(os.path.basename(video_path))[0]

    # Extract poses
    frames_data, video_fps, duration = extract_poses(video_path, sample_fps=args.fps)

    if not frames_data:
        print("ERROR: No human pose detected in video!", file=sys.stderr)
        sys.exit(1)

    # Map to Reachy joints
    choreography = map_to_reachy(frames_data, amplify=args.amplify)

    # Estimate BPM
    bpm = estimate_bpm(choreography)
    print(f"🎵 Estimated BPM: {bpm}")

    if args.preview:
        preview_choreography(choreography)

    # Save
    save_choreography(choreography, args.output, title=title, bpm=bpm)

    # Cleanup temp file
    if args.url and os.path.exists(video_path):
        os.unlink(video_path)

    print(f"\n✅ Ready! Play with: python reachy-dance.py --choreo {args.output}")


if __name__ == "__main__":
    main()
