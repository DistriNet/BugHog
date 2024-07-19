#!/bin/bash

source /app/scripts/boot/setup_environment.sh

/app/scripts/boot/manage_certs.sh

rm -f /tmp/Xvfb.pid
service xvfb start

exec python3 /app/bci/worker.py "$@"
