#!/bin/sh
# uv_update.sh
#
# Upgrades all Python dependencies and syncs the virtual environment.
# Run this locally (outside of Docker) to update uv.lock.
#
# Usage:
#   ./scripts/uv_update.sh

set -e

echo "==> Upgrading Python dependencies..."
uv lock --upgrade

echo "==> Syncing virtual environment..."
uv sync

echo "==> Done."
