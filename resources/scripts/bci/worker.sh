#!/bin/bash

source /app/setup_environment.sh

service xvfb start
python3 /app/bci/worker.py "$@"
