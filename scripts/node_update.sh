#!/bin/sh

exec docker run -v ${PWD}/bci/web/vue/:/app -w /app node:lts-alpine npm update
