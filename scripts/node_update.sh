#!/bin/sh

exec docker run -v ${PWD}/bughog/web/vue/:/app -w /app node:lts-alpine npm update
