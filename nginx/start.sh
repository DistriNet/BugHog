#!/bin/sh

rm /etc/nginx/nginx.conf;
ln /etc/nginx/config/nginx.conf /etc/nginx/nginx.conf;

if [ "$DEVELOPMENT" = "1" ]; then
    ln /etc/nginx/config/core_dev.conf /etc/nginx/config/core.conf;
else
    ln /etc/nginx/config/core_prod.conf /etc/nginx/config/core.conf;
fi

nginx -g 'daemon off;'
