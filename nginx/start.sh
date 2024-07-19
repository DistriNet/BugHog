#!/bin/sh

rm /usr/local/openresty/nginx/conf/nginx.conf;
rm /usr/local/openresty/nginx/conf/nginx.conf.default;
ln /etc/nginx/config/nginx.conf /usr/local/openresty/nginx/conf/nginx.conf;

if [ "$DEVELOPMENT" = "1" ]; then
    ln /etc/nginx/config/core_dev.conf /etc/nginx/config/core.conf;
else
    ln /etc/nginx/config/core_prod.conf /etc/nginx/config/core.conf;
fi

# Give bh_core a little bit more time to generate the certificates
sleep 1;

exec /usr/bin/openresty -g 'daemon off;'
