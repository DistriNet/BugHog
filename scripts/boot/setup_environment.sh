#!/bin/bash

export PYTHONPATH=/app
export DISPLAY=:1
# Disable content sandbox (causes trouble with older Firefox revisions) https://wiki.mozilla.org/Security/Sandbox/Seccomp
export MOZ_DISABLE_CONTENT_SANDBOX=1
export PATH="${PATH}:/$HOME/.local/bin"
