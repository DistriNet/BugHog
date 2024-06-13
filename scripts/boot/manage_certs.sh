#!/bin/sh

# Check if the CA certificate file exists
SSL_DIR="/etc/nginx/ssl";
cd "$SSL_DIR";
if [ ! -f "$SSL_DIR/certs/bughog_CA.crt" ]; then
    echo "CA certificate not found. Generating a new CA certificate.";
    "$SSL_DIR/generate_CA.sh";
    chmod 600 "$SSL_DIR/certs/bughog_CA.crt";
else
    echo "CA certificate already exists.";
fi
echo "Generating domain certificates";
"$SSL_DIR/generate_certs.sh";
cd /app

# Add certificates to browsers

# Chromium
mkdir -p $HOME/.pki/nssdb && \
certutil -d sql:$HOME/.pki/nssdb -A -t TC -n bci-ca -i /etc/nginx/ssl/certs/bughog_CA.crt && \
# Firefox
# Legacy se rity databases (cert8.db and key3.db)
certutil -A -n bci-ca -t CT,c -i /etc/nginx/ssl/certs/bughog_CA.crt -d /app/browser/profiles/firefox/default-67/ && \
certutil -A -n bci-ca -t CT,c -i /etc/nginx/ssl/certs/bughog_CA.crt -d /app/browser/profiles/firefox/tp-67/ && \
# New SQL security databases (cert9.db and key4.db)
certutil -A -n bci-ca -t CT,c -i /etc/nginx/ssl/certs/bughog_CA.crt -d sql:/app/browser/profiles/firefox/default-67/ && \
certutil -A -n bci-ca -t CT,c -i /etc/nginx/ssl/certs/bughog_CA.crt -d sql:/app/browser/profiles/firefox/tp-67/
