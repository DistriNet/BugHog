#!/bin/bash

source /app/scripts/boot/setup_environment.sh

/app/scripts/boot/manage_certs.sh

rm -f /tmp/Xvfb.pid
service xvfb start

if [ -n "$DEVELOPMENT" ]; then
    uv sync --locked
else
    uv sync --no-dev --locked
fi
exec python3 /app/bughog/worker.py "$@"
