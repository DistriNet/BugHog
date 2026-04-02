FROM node:22.14-alpine AS ui-build-stage
WORKDIR /app
COPY /bughog/web/vue/package*.json ./
RUN npm install
COPY /bughog/web/vue ./
RUN npm run build


FROM openresty/openresty:1.27.1.1-3-bullseye AS nginx
RUN apt update -y && \
    apt install -y curl && \
    rm -rf /var/lib/apt/lists/*
RUN mkdir -p /www/data/js && \
    curl https://cdn.bokeh.org/bokeh/release/bokeh-3.8.2.min.js -o /www/data/js/bokeh.min.js && \
    curl https://cdn.bokeh.org/bokeh/release/bokeh-api-3.8.2.min.js -o /www/data/js/bokeh-api.min.js
COPY ./nginx/start.sh /usr/local/bin/
COPY ./nginx/config /etc/nginx/config
COPY --from=ui-build-stage /app/dist /www/data
COPY --from=ui-build-stage /app/node_modules/ace-builds/src-min-noconflict /www/data/node_modules/ace-builds/src-min-noconflict
CMD ["start.sh"]


FROM python:3.13-slim-bullseye AS base
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /bin/
RUN apt-get update
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"


FROM base AS core
# Install Docker
RUN apt install -y \
    curl \
    docker.io \
    git \
    procps

RUN curl -sSLo builx-plugin.deb https://download.docker.com/linux/debian/dists/bullseye/pool/stable/amd64/docker-buildx-plugin_0.31.1-1~debian.11~bullseye_amd64.deb &&\
    dpkg -i builx-plugin.deb &&\
    rm builx-plugin.deb

COPY bughog pyproject.toml uv.lock /app/
RUN uv sync --no-dev --locked

COPY --chmod=0755 scripts/ /app/scripts/
COPY bughog /app/bughog
ENTRYPOINT [ "/app/scripts/boot/core.sh" ]


FROM base AS worker

COPY pyproject.toml uv.lock /app/
RUN uv sync --no-dev --locked

COPY bughog /app/bughog/
COPY --chmod=0755 scripts/ /app/scripts/
ENTRYPOINT [ "/app/scripts/boot/worker.sh" ]
