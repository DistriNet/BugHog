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
