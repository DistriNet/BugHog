#!/bin/sh
# node_update.sh
#
# Updates Node.js dependencies for the Vue frontend using a temporary Node container.
# Runs npm update inside the vue/ directory and updates package-lock.json.
#
# Usage:
#   ./scripts/node_update.sh

set -e

echo "==> Updating Node.js dependencies..."
exec docker run --rm -v ${PWD}/bughog/web/vue/:/app -w /app node:lts-alpine npm update
