#!/bin/sh

exec docker compose up --force-recreate core nginx
