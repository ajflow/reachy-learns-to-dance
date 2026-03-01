#!/bin/bash
# Run ON the Reachy Mini Pi:
#   ssh pollen@reachy-mini.local (password: root)
#   curl -sL https://moltworker.flowtivity.ai/reachy-tunnel.sh | bash
#
# Or paste this whole script and run it.
# Creates a persistent reverse tunnel so VPS can reach robot API.

VPS="52.65.224.20"
KEY_FILE="$HOME/.ssh/vps_tunnel_key"

# Write the tunnel key (restricted: tunnel only, no shell access)
mkdir -p "$HOME/.ssh"
cat > "$KEY_FILE" << 'KEYEOF'
-----BEGIN OPENSSH PRIVATE KEY-----
KEYEOF
# NOTE: Private key must be copied manually for security.
# Get it from AJ or run the setup commands below.

chmod 600 "$KEY_FILE"

echo "🤖 Connecting reverse tunnel: VPS:8000 → Robot:8000"
echo "   Press Ctrl+C to stop."

ssh -R 8000:localhost:8000 \
    -i "$KEY_FILE" \
    -N \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -o StrictHostKeyChecking=accept-new \
    ubuntu@${VPS}
