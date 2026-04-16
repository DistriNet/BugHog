#!/bin/sh
# deploy.sh [version]
#
# Deploys BugHog by pulling pre-built images from the registry.
#
# IMPORTANT: This script performs a git checkout to ensure that config files,
#            compose files, and scripts all match the deployed version.
#            Any uncommitted local changes will cause the checkout to fail.
#
# Usage:
#   ./scripts/deploy.sh           # pull and start "latest" (checks out HEAD of main branch)
#   ./scripts/deploy.sh beta      # pull and start "beta"   (checks out HEAD of beta branch)
#   ./scripts/deploy.sh dev       # pull and start "dev"    (checks out HEAD of dev branch)
#   ./scripts/deploy.sh v1.2.3    # pull and start a specific release (git checkout v1.2.3)

set -e

VERSION="${1:-latest}"

echo "==> Deploying BugHog $VERSION"

if [ "$VERSION" = "latest" ]; then
    echo "==> Checking out HEAD of main branch..."
    git checkout main
    git pull origin main
elif [ "$VERSION" = "beta" ]; then
    echo "==> Checking out HEAD of beta branch..."
    git checkout beta
    git pull origin beta
elif [ "$VERSION" = "dev" ]; then
    echo "==> Checking out HEAD of dev branch..."
    git checkout dev
    git pull origin dev
else
    echo "==> Checking out $VERSION (ensures config and scripts match the deployed version)..."
    git checkout "$VERSION"
fi

export BUGHOG_VERSION="$VERSION"
if docker info 2>/dev/null | grep -q rootless; then
    DS="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/docker.sock"
else
    DS="/var/run/docker.sock"
fi
ln -sf "$DS" .docker.sock

# Pull images before stopping to minimise downtime
echo "==> Pulling images for $VERSION..."
docker compose pull core nginx

echo "==> Stopping running containers..."
docker compose down --remove-orphans

echo "==> Starting BugHog $VERSION..."
env PWD=$PWD docker compose up -d --force-recreate core nginx

echo "==> BugHog $VERSION is up."
