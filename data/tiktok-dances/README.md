# TikTok Dance Data

3,642 keyframes extracted from 10 TikTok dance videos using MediaPipe pose estimation.

Each JSON file contains:
- `title`: Source description
- `bpm`: Detected beats per minute
- `duration`: Video duration in seconds
- `keyframes`: Array of pose data mapped to Reachy Mini movements

These were used to build the initial dance vocabulary. The final app uses the `reachy_mini_dances_library` (20 professional moves) instead, but this data demonstrates the TikTok learning pipeline.
