FROM node:22.14-alpine as ui-build-stage
WORKDIR /app
COPY /bci/web/vue/package*.json ./
RUN npm install
COPY /bci/web/vue ./
RUN npm run build


FROM openresty/openresty:1.27.1.1-3-bullseye AS nginx
RUN apt update -y && \
    apt install -y curl && \
    rm -rf /var/lib/apt/lists/*
RUN mkdir -p /www/data/js && \
    curl https://cdn.bokeh.org/bokeh/release/bokeh-3.6.1.min.js -o /www/data/js/bokeh.min.js && \
    curl https://cdn.bokeh.org/bokeh/release/bokeh-api-3.6.1.min.js -o /www/data/js/bokeh-api.min.js
COPY ./nginx/start.sh /usr/local/bin/
COPY ./nginx/config /etc/nginx/config
COPY --from=ui-build-stage /app/dist /www/data
COPY --from=ui-build-stage /app/node_modules/ace-builds/src-min-noconflict /www/data/node_modules/ace-builds/src-min-noconflict
CMD ["start.sh"]


FROM python:3.13-slim-bullseye AS base
WORKDIR /app

RUN apt-get update
RUN apt install -y curl gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libnspr4 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils libgbm-dev xvfb dbus-x11 libnss3-tools python3-pip python3-tk python3-xlib gnome-screenshot vim git procps &&\
    rm -rf /var/lib/apt/lists/*

# Install Docker
RUN curl -sSL https://get.docker.com/ | sh

# We manually install deprecated libraries for older browser versions.
# Most of them are Debian 11 (buster) packages.
# Stuff needed for chrome versions < 40
RUN curl -sSLo multiarch-support.deb http://security.debian.org/debian-security/pool/updates/main/g/glibc/multiarch-support_2.28-10+deb10u4_amd64.deb &&\
    curl -sSLo libgcrypt11.deb https://launchpadlibrarian.net/201289896/libgcrypt11_1.5.3-2ubuntu4.2_amd64.deb &&\
    curl -sSLo libudev0.deb https://launchpad.net/ubuntu/+source/udev/175-0ubuntu9/+build/3386050/+files/libudev0_175-0ubuntu9_amd64.deb &&\
    curl -sSLo libpng12.deb http://mirrors.kernel.org/ubuntu/pool/main/libp/libpng/libpng12-0_1.2.54-1ubuntu1_amd64.deb &&\
    curl -sSLo pango1.0.deb http://ftp.de.debian.org/debian/pool/main/p/pango1.0/libpango-1.0-0_1.42.4-8~deb10u1_amd64.deb &&\
    curl -sSLo libpangocairo-1.deb http://ftp.de.debian.org/debian/pool/main/p/pango1.0/libpangocairo-1.0-0_1.42.4-8~deb10u1_amd64.deb &&\
    curl -sSLo libpangoft2.deb http://ftp.de.debian.org/debian/pool/main/p/pango1.0/libpangoft2-1.0-0_1.42.4-8~deb10u1_amd64.deb &&\
    curl -sSLo libgtk-3.deb http://ftp.de.debian.org/debian/pool/main/g/gtk+3.0/libgtk-3-0_3.24.5-1_amd64.deb &&\
    dpkg -i multiarch-support.deb &&\
    dpkg -i libgtk-3.deb libpangoft2.deb libpangocairo-1.deb pango1.0.deb libgcrypt11.deb libudev0.deb libpng12.deb &&\
    rm multiarch-support.deb libgtk-3.deb libpangoft2.deb libpangocairo-1.deb pango1.0.deb libgcrypt11.deb libudev0.deb libpng12.deb &&\
# Stuff needed for chrome versions < 17
    ln -s /usr/lib/x86_64-linux-gnu/libnss3.so /usr/lib/x86_64-linux-gnu/libnss3.so.1d  &&\
    ln -s /usr/lib/x86_64-linux-gnu/libnssutil3.so /usr/lib/x86_64-linux-gnu/libnssutil3.so.1d  &&\
    ln -s /usr/lib/x86_64-linux-gnu/libsmime3.so /usr/lib/x86_64-linux-gnu/libsmime3.so.1d  &&\
    ln -s /usr/lib/x86_64-linux-gnu/libssl3.so /usr/lib/x86_64-linux-gnu/libssl3.so.1d  &&\
    ln -s /usr/lib/x86_64-linux-gnu/libplds4.so /usr/lib/x86_64-linux-gnu/libplds4.so.0d  &&\
    ln -s /usr/lib/x86_64-linux-gnu/libplc4.so /usr/lib/x86_64-linux-gnu/libplc4.so.0d  &&\
    ln -s /usr/lib/x86_64-linux-gnu/libnspr4.so /usr/lib/x86_64-linux-gnu/libnspr4.so.0d

RUN mkdir -p /app/logs && \
    mkdir -p /app/browser/binaries/chromium/downloaded && \
    mkdir -p /app/browser/binaries/firefox/downloaded && \
    mkdir -p /app/browser/binaries/chromium/artisanal && \
    mkdir -p /app/browser/binaries/firefox/artisanal

COPY browser/profiles /app/browser/profiles
COPY --chmod=0755 scripts/ /app/scripts/
RUN cp /app/scripts/daemon/xvfb /etc/init.d/xvfb

# Install python packages
COPY requirements.txt /app/requirements.txt
RUN pip install --user -r /app/requirements.txt

# Initiate PyAutoGUI
RUN touch /root/.Xauthority && \
    xauth add ${HOST}:0 . $(xxd -l 16 -p /dev/urandom)

FROM base AS core
# Copy rest of source code
COPY bci /app/bci
ENTRYPOINT [ "/app/scripts/boot/core.sh" ]


FROM base AS worker
# Copy rest of source code
COPY bci /app/bci
ENTRYPOINT [ "/app/scripts/boot/worker.sh" ]


FROM base AS dev
COPY requirements_dev.txt /app/requirements_dev.txt
RUN pip install --user -r requirements_dev.txt
ENTRYPOINT [ "/app/scripts/boot/core.sh" ]
