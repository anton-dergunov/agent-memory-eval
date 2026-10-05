#!/bin/bash

set -e

PORT="${1:-8888}"
JUPYTER_LAB="$HOME/Library/Python/3.14/bin/jupyter-lab"

# Get the Mac's LAN IP address.
IP=$(ipconfig getifaddr en0 2>/dev/null || true)

if [ -z "$IP" ]; then
    IP=$(ipconfig getifaddr en1 2>/dev/null || true)
fi

if [ -z "$IP" ]; then
    echo "Could not determine local IP address."
    exit 1
fi

# Generate a random token.
TOKEN=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')

URL="http://${IP}:${PORT}/lab?token=${TOKEN}"

echo
echo "JupyterLab:"
echo
echo "$URL"
echo
echo "Scan this QR code with the iPad:"
echo

printf '%s' "$URL" | qrencode -t ANSIUTF8

echo
echo "Starting JupyterLab..."
echo "  Root dir : $(pwd)"
echo "  Theme    : Solarized Light (via ~/.jupyter/custom/custom.css)"
echo "  PWA tip  : In Safari → Share → 'Add to Home Screen' for full-screen"
echo

exec "$JUPYTER_LAB" \
    --ip=0.0.0.0 \
    --port="$PORT" \
    --no-browser \
    --notebook-dir="$(pwd)" \
    --ServerApp.token="$TOKEN"
