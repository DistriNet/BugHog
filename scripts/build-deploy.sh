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
export GID=$(id -g)
export DOCKER_GID=$(getent group docker | cut -d: -f3)

echo "==> Building images from current codebase (tagged as dev)..."
docker buildx bake all

echo "==> Stopping running containers..."
docker compose down --remove-orphans

echo "==> Starting BugHog dev..."
env PWD=$PWD docker compose up -d --force-recreate core nginx

echo "==> BugHog dev is up."
