#!/bin/sh

# Add certificates to browsers

# Chromium
mkdir -p $HOME/.pki/nssdb && \
certutil -d sql:$HOME/.pki/nssdb -A -t TC -n bughog_CA -i /etc/nginx/ssl/certs/bughog_CA.crt
# Firefox
# Certificates are added to the generated profiles in ./bci/browser/configuration/firefox.py

