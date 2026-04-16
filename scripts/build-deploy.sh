#!/bin/sh
# build-deploy.sh
#
# Builds the current state of the codebase and starts BugHog.
# No git checkout is performed — whatever is currently checked out will be built.
# Images are tagged as "dev".
#
# Intended for:
#   - Local development on the dev branch
#   - Quickly testing uncommitted changes
#
# Usage:
#   ./scripts/build-deploy.sh

set -e

export BUGHOG_VERSION=dev
if docker info 2>/dev/null | grep -q rootless; then
    export DOCKER_SOCKET="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/docker.sock"
else
    export DOCKER_SOCKET="/var/run/docker.sock"
fi

echo "==> Building images from current codebase (tagged as dev)..."
docker buildx bake all

echo "==> Stopping running containers..."
docker compose down --remove-orphans

echo "==> Starting BugHog dev..."
env PWD=$PWD docker compose up -d --force-recreate core nginx

echo "==> BugHog dev is up."
