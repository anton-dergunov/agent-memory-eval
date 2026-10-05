#!/bin/bash

set -e

PORT="${1:-8888}"

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

URL="http://${IP}:${PORT}/?token=${TOKEN}"

echo
echo "Jupyter Notebook:"
echo
echo "$URL"
echo
echo "Scan this QR code with the iPad:"
echo

printf '%s' "$URL" | qrencode -t ANSIUTF8

echo
echo "Starting Jupyter Notebook..."
echo

exec jupyter notebook \
    --ip=0.0.0.0 \
    --port="$PORT" \
    --no-browser \
    --NotebookApp.token="$TOKEN"

