#!/bin/sh
# node_dev.sh
#
# Starts the Node.js dev server for live frontend development.
# Intended to be used alongside the VS Code devcontainer.
#
# Usage:
#   ./scripts/node_dev.sh

set -e

echo "==> Starting Node.js dev server..."
exec docker compose up node_dev
