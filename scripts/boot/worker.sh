#!/bin/bash

source /app/scripts/boot/setup_environment.sh

if [ -n "$MANAGE_CERTS" ]; then
    /app/scripts/boot/manage_certs.sh
fi

if [ -n "$MANAGE_XVFB" ]; then
    rm -f /tmp/Xvfb.pid
    rm -f /tmp/.X1-lock
    service xvfb start
fi

if [ "$DEVELOPMENT" ]; then
    uv sync --no-dev --frozen
fi
exec python3 /app/bughog/worker.py "$@"
