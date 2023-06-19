#!/bin/bash

chown bci:bci /var/run/docker.sock
chmod -R 777 /app/binaries/chromium/artisanal
chmod -R 777 /app/binaries/firefox/artisanal
# Because `environment` in docker-compose.yml does not set vars system-wide
echo "export host_pwd=$host_pwd" >> /app/setup_environment.sh
service xvfb start
su -s /bin/bash - bci -c "source /app/setup_environment.sh && python3 /app/bci/ui/app.py"
