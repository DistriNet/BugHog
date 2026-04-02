# Docker build and release pipeline

## Overview

BugHog uses [Docker Buildx Bake](https://docs.docker.com/build/bake/) to build all images from a single `docker-bake.hcl` file at the root of the repository. Images are pushed to [Docker Hub](https://hub.docker.com/u/bughog) via GitHub Actions.

## Images

| Image | Description |
|---|---|
| `bughog/core` | Core application server |
| `bughog/nginx` | Nginx reverse proxy |
| `bughog/worker` | Default evaluation worker |
| `bughog/worker-chromium` | Chromium-specific evaluation worker |
| `bughog/worker-firefox` | Firefox-specific evaluation worker |

All images are built from a shared `base` stage defined in the root `Dockerfile`, so subject-specific worker images only need to declare their own additions on top of it.

## Branching and release strategy

| Branch / event | Images built | Tags applied |
|---|---|---|
| Push to `beta` | All | `beta` |
| Tag `vx.y.z` on `main` | All | `x.y.z`, `latest` |
| Push to `dev` | — | — |

- **`dev`** is for active development. Developers build images locally; nothing is pushed to Docker Hub.
- **`beta`** is for pre-release testing. Every push builds and overwrites the `beta` tag on Docker Hub.
- **Releases** are triggered by pushing a version tag (e.g. `v1.2.3`) on `main`. Images are tagged with the version number and `latest`.

> [!IMPORTANT]
> Because BugHog requires the repository to be cloned locally (for bind-mounted subject files and experiments), Docker image versions are tied to git tags. The `deploy.sh` script handles this automatically by checking out the matching tag before pulling:
> ```bash
> ./scripts/deploy.sh v1.2.3   # checks out v1.2.3, pulls bughog/*:v1.2.3, starts BugHog
> ./scripts/deploy.sh          # checks out main, pulls bughog/*:latest, starts BugHog
> ```
> This keeps the repository contents and Docker images in sync.

## Building locally

To build all images on your machine:

```bash
docker buildx bake              # builds core + nginx + default worker
docker buildx bake subjects     # builds subject workers only
docker buildx bake all          # builds everything (used by build-deploy.sh)
```

The `BUGHOG_VERSION` variable controls the image tag (defaults to `dev`):

```bash
BUGHOG_VERSION=1.2.3 docker buildx bake all
```

## Adding a new subject worker

Subject worker images are never built at runtime. They must be built beforehand (via `build-deploy.sh` locally, or via the CI pipeline for releases) and are either found locally or pulled from Docker Hub when experiments start.

1. Create a Dockerfile at `subject/{type}/docker/Dockerfile.{name}`. Start from the shared base:
   ```dockerfile
   FROM base

   RUN apt-get install -y <subject-specific packages>
   ```
   Browser-based subjects typically need two optional boot behaviours, controlled by environment variables:
   - `MANAGE_CERTS=1` — runs certificate setup (requires `libnss3-tools` / `certutil`)
   - `MANAGE_XVFB=1` — starts a virtual display via Xvfb (requires `xvfb` and the init script at `/etc/init.d/xvfb`)

   ```dockerfile
   FROM base

   ENV MANAGE_CERTS=1 MANAGE_XVFB=1

   RUN apt-get install -y <subject-specific packages> libnss3-tools xvfb ...
   ```

2. Add a target and include it in the `subjects` group in `docker-bake.hcl`:
   ```hcl
   target "worker-{name}" {
     context    = "."
     dockerfile = "subject/{type}/docker/Dockerfile.{name}"
     contexts   = { base = "target:base" }
     tags       = tags("bughog/worker-{name}")
   }

   group "subjects" {
     targets = ["worker-chromium", "worker-firefox", "worker-{name}"]
   }
   ```

## GitHub Actions

The workflow is defined in `.github/workflows/build-and-push.yml`. It requires two secrets configured in the repository settings:

| Secret | Description |
|---|---|
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token (not your password) |
