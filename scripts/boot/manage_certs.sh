#!/bin/sh

# Add certificates to browsers

# Chromium
mkdir -p $HOME/.pki/nssdb && \
certutil -d sql:$HOME/.pki/nssdb -A -t TC -n bughog_CA -i /etc/nginx/ssl/certs/bughog_CA.crt && \
# Firefox
# Legacy se rity databases (cert8.db and key3.db)
certutil -A -n bughog_CA -t CT,c -i /etc/nginx/ssl/certs/bughog_CA.crt -d /app/browser/profiles/firefox/default-67/ && \
certutil -A -n bughog_CA -t CT,c -i /etc/nginx/ssl/certs/bughog_CA.crt -d /app/browser/profiles/firefox/tp-67/ && \
# New SQL security databases (cert9.db and key4.db)
certutil -A -n bughog_CA -t CT,c -i /etc/nginx/ssl/certs/bughog_CA.crt -d sql:/app/browser/profiles/firefox/default-67/ && \
certutil -A -n bughog_CA -t CT,c -i /etc/nginx/ssl/certs/bughog_CA.crt -d sql:/app/browser/profiles/firefox/tp-67/
