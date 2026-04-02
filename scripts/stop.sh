#!/bin/sh
# stop.sh
#
# Stops all BugHog containers, including worker containers spawned dynamically
# by the worker manager (which are not managed by Docker Compose).

set -e

echo "==> Stopping worker containers..."
docker ps -q --filter label=bh_worker | xargs -r docker rm -f

echo "==> Stopping core, nginx and devcontainer services (if running)..."
docker compose --profile prod --profile dev down --remove-orphans

echo "==> All BugHog containers stopped."
