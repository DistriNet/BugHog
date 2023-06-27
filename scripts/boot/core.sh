#!/bin/bash

chown bci:bci /var/run/docker.sock
chmod -R 777 /app/browser/binaries/chromium/artisanal
chmod -R 777 /app/browser/binaries/firefox/artisanal
# Because `environment` in docker-compose.yml does not set vars system-wide
echo "export host_pwd=$host_pwd" >> /app/scripts/boot/setup_environment.sh

rm -f /tmp/Xvfb.pid
rm -f /tmp/.X1-lock
service xvfb start

su -s /bin/bash - bci -c "source /app/scripts/boot/setup_environment.sh && python3 /app/bci/ui/app.py"
