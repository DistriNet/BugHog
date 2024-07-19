#!/bin/sh

PWD=$PWD exec docker compose up -d --force-recreate core nginx
