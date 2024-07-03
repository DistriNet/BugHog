#!/bin/bash

source /app/scripts/boot/setup_environment.sh

chmod -R 777 /app/browser/binaries/chromium/artisanal
chmod -R 777 /app/browser/binaries/firefox/artisanal

/app/scripts/boot/generate_certs.sh
/app/scripts/boot/manage_certs.sh

rm -f /tmp/Xvfb.pid
rm -f /tmp/.X1-lock
service xvfb start

if [[ "$DEVELOPMENT" == "1" ]]; then
    sleep infinity;
else
    gunicorn 'bci.app:create_app()' \
        --name core \
        --workers 1 \
        --threads 100 \
        --bind '0.0.0.0:5000' \
        --access-logfile /app/logs/gunicorn_access.log \
        --log-file /app/logs/gunicorn.log \
        --log-level info
fi
