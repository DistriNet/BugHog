variable "BUGHOG_VERSION" {
  default = "dev"
}

variable "ADDITIONAL_TAG" {
  default = ""
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

target "python-app" {
  context    = "."
  dockerfile = "Dockerfile"
  target     = "python-app"
}

# ──────────────────────────────────────────────
# Core images
# ──────────────────────────────────────────────

target "core" {
  context    = "."
  dockerfile = "Dockerfile"
  target     = "core"
  tags       = tags("bughog/core")
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
}

# ──────────────────────────────────────────────
# Subject workers
# ──────────────────────────────────────────────

target "worker-chromium" {
  context    = "."
  dockerfile = "subject/web_browser/docker/Dockerfile.chromium"
  contexts   = {
    base       = "target:base"
    python-app = "target:python-app"
  }
  tags       = tags("bughog/worker-chromium")
}

target "worker-firefox" {
  context    = "."
  dockerfile = "subject/web_browser/docker/Dockerfile.firefox"
  contexts   = {
    base       = "target:base"
    python-app = "target:python-app"
  }
  tags       = tags("bughog/worker-firefox")
}

target "worker-servo" {
  context    = "."
  dockerfile = "subject/web_browser/docker/Dockerfile.servo"
  contexts   = {
    python-app = "target:python-app"
  }
  tags       = tags("bughog/worker-servo")
}

target "worker-wasmtime" {
  context    = "."
  dockerfile = "subject/wasm_runtime/docker/Dockerfile.wasmtime"
  contexts   = {
    python-app = "target:python-app"
  }
  tags       = tags("bughog/worker-wasmtime")
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
