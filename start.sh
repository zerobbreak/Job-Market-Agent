#!/bin/bash
# Start Flask in background
# Note: removed --daemon to allow signal handling via supervisor or just shell tracking
# However, for this simple script, we run gunicorn in background and nginx in foreground
# to keep the container alive.
gunicorn api_server:app --bind 127.0.0.1:8000 --timeout 300 &

# Start nginx in foreground
nginx -g "daemon off;"
