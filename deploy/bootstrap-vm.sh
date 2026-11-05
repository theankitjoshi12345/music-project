#!/usr/bin/env bash
# VM startup script; runs only after an operator provisions the approved VM.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends docker.io docker-compose-v2 ca-certificates curl
systemctl enable --now docker
install -d -m 0750 /srv/music-companion /srv/music-companion/backups /srv/music-companion/releases
install -d -m 0750 -o 10001 -g 10001 /srv/music-companion/data
install -d -m 0755 /srv/music-companion/caddy-data /srv/music-companion/caddy-config
