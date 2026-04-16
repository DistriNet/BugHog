FROM node:22.14-alpine AS ui-build-stage
WORKDIR /app
COPY /bughog/web/vue/package*.json ./
RUN npm install
COPY /bughog/web/vue ./
RUN npm run build


FROM openresty/openresty:1.27.1.1-3-bullseye AS nginx
ADD https://cdn.bokeh.org/bokeh/release/bokeh-3.8.2.min.js /www/data/js/bokeh.min.js
ADD https://cdn.bokeh.org/bokeh/release/bokeh-api-3.8.2.min.js /www/data/js/bokeh-api.min.js
COPY ./nginx/start.sh /usr/local/bin/
COPY ./nginx/config /etc/nginx/config
COPY --from=ui-build-stage /app/dist /www/data
COPY --from=ui-build-stage /app/node_modules/ace-builds/src-min-noconflict /www/data/node_modules/ace-builds/src-min-noconflict
CMD ["start.sh"]


FROM python:3.13-slim-bullseye AS base

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"
ARG UID=1000 \
    GID=1000

RUN apt-get update && \
    groupadd -g $GID bughog && \
    useradd -u $UID -g $GID -m bughog

COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /bin/
COPY pyproject.toml uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen

COPY --chown=bughog:bughog --chmod=0755 scripts/ /app/scripts/
COPY --chown=bughog:bughog bughog /app/bughog/


FROM base AS core

# Install docker cli
RUN apt-get install -y curl gnupg && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/docker.gpg] https://download.docker.com/linux/debian bullseye stable" \
    > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    apt-get remove -y --autoremove curl gnupg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Give bughog access to the Docker socket (GID must match host's docker group)
ARG DOCKER_GID=999
RUN conflict=$(getent group ${DOCKER_GID} | cut -d: -f1); \
    [ -n "$conflict" ] && [ "$conflict" != "docker" ] && groupmod -g 65534 "$conflict"; \
    getent group docker > /dev/null || groupadd docker; \
    groupmod -g ${DOCKER_GID} docker && usermod -aG docker bughog

USER bughog
ENTRYPOINT [ "/app/scripts/boot/core.sh" ]


FROM base AS worker

USER bughog
ENTRYPOINT [ "/app/scripts/boot/worker.sh" ]
