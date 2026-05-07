#!/bin/sh
# stop.sh
#
# Stops all BugHog containers, including worker containers spawned dynamically
# by the worker manager (which are not managed by Docker Compose).

set -e

echo "==> Stopping worker containers..."
docker ps -q --filter label=bh_worker | xargs -r docker rm -f

echo "==> Stopping MongoDB container (if running)..."
if [ -n "$(docker ps -aq --filter name=^bh_db$)" ]; then
    docker rm -f bh_db
    echo "    Stopped bh_db."
else
    echo "    bh_db not running, skipping."
fi

echo "==> Stopping core, nginx and devcontainer services (if running)..."
docker compose --profile prod --profile dev down --remove-orphans

echo "==> All BugHog containers stopped."
