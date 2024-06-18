#!/bin/sh

# Generate a private key
openssl genrsa -out keys/bughog_CA.key 2048

# Generate root certificate
openssl req -x509 -new -nodes -key keys/bughog_CA.key -sha256 -days 7300 -config bughog.cnf -out keys/bughog_CA.pem
openssl x509 -outform der -in keys/bughog_CA.pem -out certs/bughog_CA.crt
