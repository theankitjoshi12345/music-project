#!/usr/bin/env bash
# Run on the VM as root. Registry password is read from stdin, never an argument.
set -euo pipefail
umask 077

[[ ${EUID} -eq 0 ]] || { printf '%s\n' 'Run with sudo on the deployment VM.' >&2; exit 2; }
release_sha=${1:-}
[[ $release_sha =~ ^[0-9a-f]{40}$ ]] || { printf '%s\n' 'Pass the full lowercase commit SHA.' >&2; exit 2; }
: "${REGISTRY_IMAGE:?Set the GitLab registry project path}"
: "${REGISTRY_USER:?Set the temporary CI registry username}"
: "${PUBLIC_HOST:?Set the actual public DNS hostname}"
: "${ACME_EMAIL:?Set the certificate account contact email}"
[[ $REGISTRY_IMAGE =~ ^[a-zA-Z0-9.-]+(:[0-9]+)?/[a-zA-Z0-9_./-]+$ ]] || { printf '%s\n' 'Invalid registry path.' >&2; exit 2; }
[[ $PUBLIC_HOST =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]+\.[a-zA-Z]+$ ]] || { printf '%s\n' 'Invalid public hostname.' >&2; exit 2; }
[[ $ACME_EMAIL =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+$ ]] || { printf '%s\n' 'Invalid ACME contact.' >&2; exit 2; }

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source_root=$(cd -- "$script_dir/.." && pwd)
readonly app_root=/srv/music-companion
readonly release_dir="$app_root/releases/$release_sha"
install -d -m 0750 "$app_root" "$app_root/releases" "$app_root/backups"
exec 9>"$app_root/deployment.lock"
flock -n 9 || { printf '%s\n' 'Another deployment is running.' >&2; exit 2; }
install -d -m 0750 -o 10001 -g 10001 "$app_root/data"
install -d -m 0755 "$app_root/caddy-data" "$app_root/caddy-config"
install -d -m 0750 "$release_dir/docker"
install -m 0640 "$source_root/compose.production.yaml" "$release_dir/compose.production.yaml"
install -m 0640 "$source_root/docker/Caddyfile" "$release_dir/docker/Caddyfile"

# Only non-secret configuration is persisted here. The Django key is generated
# by the backend entrypoint inside the private persistent data directory.
printf 'BACKEND_IMAGE=%s/backend:%s\nFRONTEND_IMAGE=%s/frontend:%s\nPUBLIC_HOST=%s\nACME_EMAIL=%s\n' \
  "$REGISTRY_IMAGE" "$release_sha" "$REGISTRY_IMAGE" "$release_sha" "$PUBLIC_HOST" "$ACME_EMAIL" > "$release_dir/release.env"
compose=(docker compose --env-file "$release_dir/release.env" -f "$release_dir/compose.production.yaml")
"${compose[@]}" config --quiet

registry_password=
IFS= read -r registry_password || [[ -n $registry_password ]]
[[ -n $registry_password ]] || { printf '%s\n' 'Supply the short-lived registry password on stdin.' >&2; exit 2; }
DOCKER_CONFIG=$(mktemp -d)
export DOCKER_CONFIG
cleanup() { rm -rf -- "$DOCKER_CONFIG"; }
trap cleanup EXIT
printf '%s' "$registry_password" | docker login "${REGISTRY_IMAGE%%/*}" --username "$REGISTRY_USER" --password-stdin
unset registry_password
"${compose[@]}" pull

# Refuse another backup before consuming the reserved storage budget. Retention
# is an operator decision; never silently remove user data or earlier backups.
data_kib=$(du -sk "$app_root/data" | awk '{print $1}')
backup_kib=$(du -sk "$app_root/backups" | awk '{print $1}')
free_kib=$(df -Pk "$app_root" | awk 'NR == 2 {print $4}')
estimated_backup_kib=$((data_kib + 1024))
if (( backup_kib + estimated_backup_kib > 2097152 )); then
  printf '%s\n' 'Backup budget (2 GiB) would be exceeded. Export/review retained backups before deploying; none were removed.' >&2
  exit 2
fi
if (( free_kib < estimated_backup_kib + 1048576 )); then
  printf '%s\n' 'Insufficient disk headroom for a backup and 1 GiB reserve. Existing service remains running.' >&2
  exit 2
fi

# Pull first to minimize downtime. Stop all writers before the SQLite/media
# snapshot. Keep the backup even when a later deployment step fails.
"${compose[@]}" stop --timeout 750 backend
backup_file="$app_root/backups/$(date -u +%Y%m%dT%H%M%SZ)-before-$release_sha.tar.gz"
tar -C "$app_root" -czf "$backup_file" data
printf 'Data backup: %s\n' "$backup_file"
if [[ -f "$app_root/current-release" ]]; then
  cp "$app_root/current-release" "$app_root/previous-release"
fi
printf '%s\n' "$release_sha" > "$app_root/pending-release"
"${compose[@]}" up -d --wait --wait-timeout 240

# Do not disable certificate verification: a valid public TLS chain is required.
health_file=$(mktemp)
trap 'rm -f -- "$health_file"; cleanup' EXIT
curl --fail --silent --show-error --retry 12 --retry-all-errors --retry-delay 5 \
  --connect-timeout 10 --max-time 30 "https://$PUBLIC_HOST/api/health/" > "$health_file"
python3 - "$health_file" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as response:
    assert json.load(response).get("status") == "ok", "Unhealthy API response"
PY
curl --fail --silent --show-error --output /dev/null --connect-timeout 10 --max-time 30 "https://$PUBLIC_HOST/"
printf '%s\n' "$release_sha" > "$app_root/current-release"
rm -f -- "$app_root/pending-release"
printf 'Release %s passed HTTPS frontend/API checks at https://%s/\n' "$release_sha" "$PUBLIC_HOST"
printf '%s\n' 'Run the golden-path upload, recognition, privacy, and persistence checks before recording launch completion.'
