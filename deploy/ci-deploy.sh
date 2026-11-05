#!/usr/bin/env bash
# GitLab protected-main job only. No service-account key or registry password
# is written into repository files or passed as a process argument.
set -euo pipefail
umask 077

[[ ${CI:-false} == true && ${DEPLOY_ENABLED:-false} == true && ${CI_COMMIT_REF_PROTECTED:-false} == true ]] || {
  printf '%s\n' 'Deployment requires an enabled protected GitLab CI job.' >&2; exit 2;
}
[[ ${CI_COMMIT_BRANCH:-} == "${CI_DEFAULT_BRANCH:-main}" ]] || { printf '%s\n' 'Only the default branch can deploy.' >&2; exit 2; }
for variable in GCP_ID_TOKEN GCP_WIF_PROVIDER GCP_DEPLOY_SERVICE_ACCOUNT GCP_PROJECT_ID GCP_ZONE GCP_INSTANCE PUBLIC_HOST ACME_EMAIL GCP_SSH_KNOWN_HOSTS CI_REGISTRY_IMAGE CI_REGISTRY_USER CI_REGISTRY_PASSWORD CI_COMMIT_SHA CI_JOB_ID; do
  [[ -n ${!variable:-} ]] || { printf 'Missing CI variable: %s\n' "$variable" >&2; exit 2; }
done
[[ $CI_COMMIT_SHA =~ ^[0-9a-f]{40}$ && $CI_JOB_ID =~ ^[0-9]+$ ]] || { printf '%s\n' 'Invalid GitLab release identity.' >&2; exit 2; }
[[ $GCP_INSTANCE =~ ^[a-z][a-z0-9-]{0,62}$ ]] || { printf '%s\n' 'Invalid VM name.' >&2; exit 2; }
[[ -f $GCP_SSH_KNOWN_HOSTS ]] || { printf '%s\n' 'GCP_SSH_KNOWN_HOSTS must be a protected GitLab file variable.' >&2; exit 2; }

temporary_dir=$(mktemp -d)
trap 'rm -rf -- "$temporary_dir"' EXIT
export CLOUDSDK_CONFIG="$temporary_dir/gcloud"
printf '%s' "$GCP_ID_TOKEN" > "$temporary_dir/oidc-token"
gcloud iam workload-identity-pools create-cred-config "$GCP_WIF_PROVIDER" \
  --service-account="$GCP_DEPLOY_SERVICE_ACCOUNT" \
  --credential-source-file="$temporary_dir/oidc-token" \
  --output-file="$temporary_dir/credential.json"
gcloud auth login --cred-file="$temporary_dir/credential.json" --quiet
gcloud config set project "$GCP_PROJECT_ID" --quiet

ssh-keygen -q -t ed25519 -N '' -f "$temporary_dir/ssh-key"
cp "$GCP_SSH_KNOWN_HOSTS" "$temporary_dir/known_hosts"
connection=(--project="$GCP_PROJECT_ID" --zone="$GCP_ZONE" --tunnel-through-iap --quiet
  --ssh-key-file="$temporary_dir/ssh-key" --ssh-key-expire-after=1h --strict-host-key-checking=yes)

stage_name="music-companion-ci-$CI_JOB_ID"
install -d -m 0750 "$temporary_dir/$stage_name/deploy" "$temporary_dir/$stage_name/docker"
install -m 0640 compose.production.yaml "$temporary_dir/$stage_name/compose.production.yaml"
install -m 0640 docker/Caddyfile "$temporary_dir/$stage_name/docker/Caddyfile"
install -m 0640 deploy/release.sh "$temporary_dir/$stage_name/deploy/release.sh"
gcloud compute scp "${connection[@]}" --scp-flag="-oUserKnownHostsFile=$temporary_dir/known_hosts" \
  --recurse "$temporary_dir/$stage_name" "$GCP_INSTANCE:~/"

# printf %q is shell escaping for the known Bash login shell on the Ubuntu VM.
# Only non-secret values enter this command. The one-use registry password is
# forwarded separately over the authenticated SSH channel on stdin.
printf -v remote_environment 'REGISTRY_IMAGE=%q REGISTRY_USER=%q PUBLIC_HOST=%q ACME_EMAIL=%q' \
  "$CI_REGISTRY_IMAGE" "$CI_REGISTRY_USER" "$PUBLIC_HOST" "$ACME_EMAIL"
printf -v remote_script 'set -e; trap '\''rm -rf -- "$HOME/%s"'\'' EXIT; sudo -n env %s bash "$HOME/%s/deploy/release.sh" %q' \
  "$stage_name" "$remote_environment" "$stage_name" "$CI_COMMIT_SHA"
printf -v remote_command 'bash -c %q' "$remote_script"
printf '%s\n' "$CI_REGISTRY_PASSWORD" | gcloud compute ssh "$GCP_INSTANCE" "${connection[@]}" \
  --ssh-flag="-oUserKnownHostsFile=$temporary_dir/known_hosts" --command="$remote_command" -- -T
