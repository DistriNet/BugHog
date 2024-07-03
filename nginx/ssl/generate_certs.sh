#!/bin/sh

# Create a certificate-signing request
openssl req -out certs/bughog.csr -newkey rsa:2048 -nodes -keyout keys/bughog.key -config bughog.cnf

# Create the signed certificate
openssl x509 -req -in certs/bughog.csr -CA keys/bughog_CA.pem -CAkey keys/bughog_CA.key -CAcreateserial -out certs/bughog.crt -days 7300 -sha256 -extfile bughog.ext
