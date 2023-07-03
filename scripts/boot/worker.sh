#!/bin/bash

source /app/scripts/boot/setup_environment.sh

rm -f /tmp/Xvfb.pid
service xvfb start

python3 /app/bci/worker.py "$@"
