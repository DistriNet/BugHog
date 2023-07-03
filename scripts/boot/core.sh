#!/bin/bash

chmod -R 777 /app/browser/binaries/chromium/artisanal
chmod -R 777 /app/browser/binaries/firefox/artisanal

rm -f /tmp/Xvfb.pid
rm -f /tmp/.X1-lock
service xvfb start

source /app/scripts/boot/setup_environment.sh
python3 /app/bci/ui/app.py
