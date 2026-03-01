# Reachy Mini REST API Reference

## Base URL
`http://{REACHY_HOST}:8000/api` (default: `reachy-mini.local:8000`)

## Movement Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/move/goto` | POST | Smooth interpolated move (head, antennas, body) |
| `/move/set_target` | POST | Instant target (for control loops at 10Hz+) |
| `/move/play/wake_up` | POST | Wake robot up |
| `/move/play/goto_sleep` | POST | Put robot to sleep |
| `/move/play/recorded-move-dataset/{dataset}/{move}` | POST | Play recorded emotion/move |
| `/move/running` | GET | List running moves |
| `/move/stop` | POST | Stop all moves |

## State Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/state/full` | GET | Complete robot state (head, body, antennas, motors) |
| `/state/present_head_pose` | GET | Current head pose |
| `/state/present_body_yaw` | GET | Current body rotation |
| `/state/present_antenna_joint_positions` | GET | Antenna positions |
| `/state/doa` | GET | Direction of arrival (mic array) |

## Motor Control

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/motors/status` | GET | Motor status |
| `/motors/set_mode/{mode}` | POST | Set mode: `enabled`, `disabled`, `gravity_compensation` |

## WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `ws://.../api/state/ws/full` | Real-time state stream |
| `ws://.../api/move/ws/updates` | Movement events |
| `ws://.../api/move/ws/set_target` | Stream target commands |

## Safety Limits

| Joint | Range |
|-------|-------|
| Head pitch/roll | [-40, +40] degrees |
| Head yaw | [-180, +180] degrees |
| Body yaw | [-160, +160] degrees |
| Yaw delta (head - body) | Max 65 degrees |

## goto Request Body

```json
{
  "head_pose": {"yaw": 0, "pitch": 0, "roll": 0},
  "antennas": [0, 0],
  "body_yaw": 0,
  "duration": 1.0,
  "method": "minjerk"
}
```

Interpolation methods: `linear`, `minjerk` (default), `ease_in_out`, `cartoon`

## Emotions Library

Dataset: `pollen-robotics/reachy-mini-emotions-library`
Available emotions: `happy`, `sad`, `surprised`, `angry`, `confused`, `thinking`, `excited`

## Interactive Docs

When the robot daemon is running: `http://{REACHY_HOST}:8000/docs` (Swagger UI)
