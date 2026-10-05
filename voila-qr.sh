#!/bin/bash

set -e

# Usage: voila-qr.sh [notebook.ipynb] [port]
#   If no notebook is given, Voilà shows a directory listing.
NOTEBOOK="${1:-}"
PORT="${2:-8866}"

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

if [ -n "$NOTEBOOK" ]; then
    URL="http://${IP}:${PORT}/voila/render/$(basename "$NOTEBOOK")?token=${TOKEN}"
else
    URL="http://${IP}:${PORT}/?token=${TOKEN}"
fi

echo
echo "Voilà Notebook Viewer:"
echo
echo "$URL"
echo
echo "Scan this QR code with the iPad:"
echo

printf '%s' "$URL" | qrencode -t ANSIUTF8

echo
echo "Starting Voilà..."
echo
echo "Tip: In Safari, tap Share → 'Add to Home Screen' for full-screen PWA mode."
echo

if [ -n "$NOTEBOOK" ]; then
    exec voila "$NOTEBOOK" \
        --port="$PORT" \
        --no-browser \
        --Voila.ip=0.0.0.0 \
        --ServerApp.token="$TOKEN"
else
    exec voila \
        --port="$PORT" \
        --no-browser \
        --Voila.ip=0.0.0.0 \
        --ServerApp.token="$TOKEN"
fi
