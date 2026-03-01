#!/bin/bash
# Reverse SSH tunnel: Reachy Mini Pi → VPS
#
# Run ON the Pi:
#   ssh pollen@reachy-mini.local
#   bash setup-tunnel.sh
#
# Creates a persistent reverse tunnel so the VPS can reach:
#   - Port 8000: Reachy Mini REST API
#   - Port 2222: SSH access to Pi
#   - Port 8001: DJ Dashboard

VPS_HOST="${VPS_HOST:-your-vps-ip}"
KEY_FILE="${KEY_FILE:-$HOME/.ssh/vps_key}"

if [ ! -f "$KEY_FILE" ]; then
    echo "Error: SSH key not found at $KEY_FILE"
    echo "Generate one: ssh-keygen -t ed25519 -f $KEY_FILE -N ''"
    echo "Then add the public key to your VPS authorized_keys"
    exit 1
fi

echo "Connecting reverse tunnel to $VPS_HOST..."
echo "  VPS:8000 → Robot API"
echo "  VPS:2222 → Robot SSH"
echo "  VPS:8001 → DJ Dashboard"
echo "Press Ctrl+C to stop."

ssh -R 8000:localhost:8000 \
    -R 2222:localhost:22 \
    -R 8001:localhost:8001 \
    -i "$KEY_FILE" \
    -N \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -o StrictHostKeyChecking=accept-new \
    "ubuntu@${VPS_HOST}"
