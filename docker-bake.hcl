variable "BUGHOG_VERSION" {
  default = "dev"
}

variable "ADDITIONAL_TAG" {
  default = ""
}

variable "UID" {
  default = 1000
}

variable "GID" {
  default = 1000
}

variable "DOCKER_GID" {
  default = 999
}

function "tags" {
  params = [image]
  result = ADDITIONAL_TAG != "" ? ["${image}:${BUGHOG_VERSION}", "${image}:${ADDITIONAL_TAG}"] : ["${image}:${BUGHOG_VERSION}"]
}

# ──────────────────────────────────────────────
# Shared base (not tagged/pushed)
# ──────────────────────────────────────────────

target "base" {
  context    = "."
  dockerfile = "Dockerfile"
  target     = "base"
}

# ──────────────────────────────────────────────
# Core images
# ──────────────────────────────────────────────

target "core" {
  context    = "."
  dockerfile = "Dockerfile"
  target     = "core"
  tags       = tags("bughog/core")
  args       = {
    UID        = UID
    GID        = GID
    DOCKER_GID = DOCKER_GID
  }
}

target "nginx" {
  context    = "."
  dockerfile = "Dockerfile"
  target     = "nginx"
  tags       = tags("bughog/nginx")
}

target "worker" {
  context    = "."
  dockerfile = "Dockerfile"
  target     = "worker"
  tags       = tags("bughog/worker")
  args       = {
    UID = UID
    GID = GID
  }
}

# ──────────────────────────────────────────────
# Subject workers
# ──────────────────────────────────────────────

target "worker-chromium" {
  context    = "."
  dockerfile = "subject/web_browser/docker/Dockerfile.chromium"
  contexts   = {
    base = "target:base"
  }
  tags       = tags("bughog/worker-chromium")
}

target "worker-firefox" {
  context    = "."
  dockerfile = "subject/web_browser/docker/Dockerfile.firefox"
  contexts   = {
    base = "target:base"
  }
  tags       = tags("bughog/worker-firefox")
}

target "worker-servo" {
  context    = "."
  dockerfile = "subject/web_browser/docker/Dockerfile.servo"
  tags       = tags("bughog/worker-servo")
  args       = {
    UID = UID
    GID = GID
  }
}

target "worker-wasmtime" {
  context    = "."
  dockerfile = "subject/wasm_runtime/docker/Dockerfile.wasmtime"
  tags       = tags("bughog/worker-wasmtime")
  args       = {
    UID = UID
    GID = GID
  }
}

# ──────────────────────────────────────────────
# Groups
# ──────────────────────────────────────────────

group "default" {
  targets = ["core", "nginx", "worker"]
}

group "subjects" {
  targets = ["worker-chromium", "worker-firefox", "worker-servo", "worker-wasmtime"]
}

group "all" {
  targets = ["default", "subjects"]
}
