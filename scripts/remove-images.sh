#!/bin/sh
# remove-images.sh
#
# Removes all locally built BugHog Docker images.
# Matches images named bughog/* (bake), bughog-* (compose), and bh_core_dev (devcontainer).
# Does not affect running containers — run stop.sh first if needed.
#
# Usage:
#   ./scripts/remove-images.sh

set -e

images=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep -E '^(bughog/|bughog-|bh_core_dev)')

if [ -z "$images" ]; then
    echo "==> No BugHog images found."
    exit 0
fi

echo "==> Found the following BugHog images:"
echo "$images" | sed 's/^/     /'

echo "==> Removing BugHog images..."
echo "$images" | xargs docker rmi -f

echo "==> Done."
