#!/usr/bin/env bash
# Protected-main Cloud Run and Firebase Hosting deployment. This is inert until
# the owner-approved GitLab variables enable it. No service-account key is used.
set -euo pipefail
umask 077

[[ ${CI:-false} == true && ${DEPLOY_ENABLED:-false} == true && ${CI_COMMIT_REF_PROTECTED:-false} == true ]] || {
  printf '%s\n' 'Deployment requires an enabled protected GitLab CI job.' >&2; exit 2;
}
[[ ${CLEAN_ARTIFACT_IMAGE:-false} == true ]] || {
  printf '%s\n' 'CLEAN_ARTIFACT_IMAGE=true is required for the approved temporary-image cleanup.' >&2; exit 2;
}
[[ ${CI_COMMIT_BRANCH:-} == "${CI_DEFAULT_BRANCH:-main}" ]] || {
  printf '%s\n' 'Only the protected default branch can deploy.' >&2; exit 2;
}
for variable in GCP_ID_TOKEN GCP_WIF_PROVIDER GCP_DEPLOY_SERVICE_ACCOUNT GCP_RUNTIME_SERVICE_ACCOUNT \
  GCP_PROJECT_ID GCP_REGION GCP_CLOUD_RUN_SERVICE GCP_ARTIFACT_REPOSITORY GCP_STORAGE_BUCKET \
  GCP_FIREBASE_SITE GCP_DJANGO_SECRET GOOGLE_OAUTH_CLIENT_ID CI_REGISTRY_IMAGE CI_REGISTRY_USER CI_REGISTRY_PASSWORD \
  CI_COMMIT_SHA; do
  [[ -n ${!variable:-} ]] || { printf 'Missing CI variable: %s\n' "$variable" >&2; exit 2; }
done
[[ $CI_COMMIT_SHA =~ ^[0-9a-f]{40}$ ]] || { printf '%s\n' 'Invalid commit SHA.' >&2; exit 2; }
[[ $GCP_REGION =~ ^[a-z]+-[a-z]+[0-9]$ ]] || { printf '%s\n' 'Invalid Google Cloud region.' >&2; exit 2; }
[[ $GCP_CLOUD_RUN_SERVICE =~ ^[a-z][a-z0-9-]{0,62}$ ]] || { printf '%s\n' 'Invalid Cloud Run service.' >&2; exit 2; }
[[ $GCP_ARTIFACT_REPOSITORY =~ ^[a-z][a-z0-9-]{0,62}$ ]] || { printf '%s\n' 'Invalid Artifact Registry repository.' >&2; exit 2; }
[[ $GCP_REGION == us-central1 && $GCP_CLOUD_RUN_SERVICE == music-companion-api ]] || {
  printf '%s\n' 'firebase.json expects music-companion-api in us-central1.' >&2; exit 2;
}
[[ $GCP_FIREBASE_SITE == "$GCP_PROJECT_ID" ]] || {
  printf '%s\n' 'The production Firebase site must match the Google Cloud project ID.' >&2; exit 2;
}

temporary_dir=$(mktemp -d)
immutable_image=''
guard_immutable_image=''
cleanup() {
  status=$?
  set +e
  for image in "$immutable_image" "$guard_immutable_image"; do
    if [[ -n $image ]]; then
      gcloud artifacts docker images delete "$image" --delete-tags --quiet >&2 || \
        printf 'WARNING: failed to clean temporary image %s\n' "$image" >&2
    fi
  done
  rm -rf -- "$temporary_dir"
  trap - EXIT
  exit "$status"
}
trap cleanup EXIT
export CLOUDSDK_CONFIG="$temporary_dir/gcloud"
printf '%s' "$GCP_ID_TOKEN" > "$temporary_dir/oidc-token"
gcloud iam workload-identity-pools create-cred-config "$GCP_WIF_PROVIDER" \
  --service-account="$GCP_DEPLOY_SERVICE_ACCOUNT" \
  --credential-source-file="$temporary_dir/oidc-token" \
  --output-file="$temporary_dir/credential.json"
python3 - "$temporary_dir/credential.json" "$GCP_PROJECT_ID" <<'PY'
import json
import os
import sys

path, project_id = sys.argv[1:]
with open(path, encoding="utf-8") as source:
    credential = json.load(source)
credential["quota_project_id"] = project_id
with open(path, "w", encoding="utf-8") as destination:
    json.dump(credential, destination)
os.chmod(path, 0o600)
PY
gcloud auth login --cred-file="$temporary_dir/credential.json" --quiet
gcloud config set project "$GCP_PROJECT_ID" --quiet
export GOOGLE_APPLICATION_CREDENTIALS="$temporary_dir/credential.json"

# Keep required Datastore-mode composite indexes under version control. The
# command is idempotent; existing ready indexes are left unchanged.
gcloud datastore indexes create backend/index.yaml \
  --project="$GCP_PROJECT_ID" --quiet
index_ready=false
for attempt in $(seq 1 60); do
  gcloud datastore indexes list --project="$GCP_PROJECT_ID" --format=json > "$temporary_dir/datastore-indexes.json"
  if python3 - "$temporary_dir/datastore-indexes.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    indexes = json.load(source)
for index in indexes:
    names = [property_["name"] for property_ in index.get("properties", [])]
    if index.get("kind") == "scoreapi_score" and names == ["content_sha256", "owner"]:
        raise SystemExit(0 if index.get("state") == "READY" else 1)
raise SystemExit(1)
PY
  then
    index_ready=true
    break
  fi
  sleep 10
done
[[ $index_ready == true ]] || { printf '%s\n' 'Datastore upload index did not become ready.' >&2; exit 2; }

registry_host="${GCP_REGION}-docker.pkg.dev"
destination_image="$registry_host/$GCP_PROJECT_ID/$GCP_ARTIFACT_REPOSITORY/music-companion:$CI_COMMIT_SHA"
source_image="$CI_REGISTRY_IMAGE/cloudrun:$CI_COMMIT_SHA"
guard_destination_image="$registry_host/$GCP_PROJECT_ID/$GCP_ARTIFACT_REPOSITORY/music-companion-cost-guard:$CI_COMMIT_SHA"
guard_source_image="$CI_REGISTRY_IMAGE/cost-guard:$CI_COMMIT_SHA"
export GCP_ACCESS_TOKEN
GCP_ACCESS_TOKEN=$(gcloud auth print-access-token)
export CONTAINER_AUTH_FILE="$temporary_dir/containers-auth.json"
python3 - <<'PY'
import base64
import json
import os

def encoded(user, password):
    return base64.b64encode(f"{user}:{password}".encode()).decode()

gitlab_host = os.environ["CI_REGISTRY_IMAGE"].split("/", 1)[0]
gcp_host = f'{os.environ["GCP_REGION"]}-docker.pkg.dev'
authentication = {
    "auths": {
        gitlab_host: {"auth": encoded(os.environ["CI_REGISTRY_USER"], os.environ["CI_REGISTRY_PASSWORD"])},
        gcp_host: {"auth": encoded("oauth2accesstoken", os.environ["GCP_ACCESS_TOKEN"])},
    }
}
with open(os.environ["CONTAINER_AUTH_FILE"], "w", encoding="utf-8") as destination:
    json.dump(authentication, destination)
os.chmod(os.environ["CONTAINER_AUTH_FILE"], 0o600)
PY
unset GCP_ACCESS_TOKEN CI_REGISTRY_PASSWORD

# Cloud Run imports the referenced image into its own storage. Artifact
# Registry is only a short-lived handoff so the large Audiveris image never
# accumulates monthly registry storage.
skopeo copy --authfile "$CONTAINER_AUTH_FILE" "docker://$source_image" "docker://$destination_image"
immutable_image="$destination_image"
image_digest=$(skopeo inspect --authfile "$CONTAINER_AUTH_FILE" --format '{{.Digest}}' "docker://$destination_image")
[[ $image_digest =~ ^sha256:[0-9a-f]{64}$ ]] || { printf '%s\n' 'Artifact Registry returned an invalid digest.' >&2; exit 2; }
immutable_image="${destination_image%:*}@$image_digest"
skopeo copy --authfile "$CONTAINER_AUTH_FILE" "docker://$guard_source_image" "docker://$guard_destination_image"
guard_immutable_image="$guard_destination_image"
guard_image_digest=$(skopeo inspect --authfile "$CONTAINER_AUTH_FILE" --format '{{.Digest}}' "docker://$guard_destination_image")
[[ $guard_image_digest =~ ^sha256:[0-9a-f]{64}$ ]] || { printf '%s\n' 'Artifact Registry returned an invalid cost-guard digest.' >&2; exit 2; }
guard_immutable_image="${guard_destination_image%:*}@$guard_image_digest"

readonly guard_service=music-companion-cost-guard
readonly guard_runtime_account="music-companion-cost-guard@$GCP_PROJECT_ID.iam.gserviceaccount.com"
readonly guard_push_account="music-companion-guard-push@$GCP_PROJECT_ID.iam.gserviceaccount.com"
readonly budget_subscription=music-companion-cost-guard
readonly budget_topic=music-companion-budget
readonly billing_account=01124F-AA2E30-D8B14D
readonly budget_id=9f6f514b-5508-441c-ba32-249b32edf00f

# This service is private, accepts only authenticated same-project Pub/Sub
# delivery, and has only the project-level permission needed to unlink billing.
gcloud run deploy "$guard_service" \
  --project="$GCP_PROJECT_ID" \
  --region="$GCP_REGION" \
  --image="$guard_immutable_image" \
  --service-account="$guard_runtime_account" \
  --no-allow-unauthenticated \
  --ingress=internal \
  --execution-environment=gen2 \
  --port=8080 \
  --cpu=1 \
  --memory=512Mi \
  --concurrency=1 \
  --timeout=30 \
  --min=0 \
  --max=1 \
  --no-cpu-boost \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$GCP_PROJECT_ID,EXPECTED_BUDGET_ID=$budget_id,EXPECTED_BILLING_ACCOUNT_ID=$billing_account,EXPECTED_BUDGET_DISPLAY_NAME=Music Companion zero-cost guard,EXPECTED_BUDGET_AMOUNT_USD=1.00" \
  --quiet

guard_service_json="$temporary_dir/guard-service.json"
gcloud run services describe "$guard_service" --project="$GCP_PROJECT_ID" \
  --region="$GCP_REGION" --format=json > "$guard_service_json"
guard_service_url=$(python3 - "$guard_service_json" "$guard_runtime_account" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    service = json.load(source)
template = service["spec"]["template"]
assert template["spec"]["serviceAccountName"] == sys.argv[2]
service_annotations = service["metadata"].get("annotations", {})
template_annotations = template["metadata"].get("annotations", {})
max_scale = service_annotations.get(
    "run.googleapis.com/maxScale",
    template_annotations.get("autoscaling.knative.dev/maxScale"),
)
min_scale = service_annotations.get(
    "run.googleapis.com/minScale",
    template_annotations.get("autoscaling.knative.dev/minScale", "0"),
)
assert max_scale == "1"
assert min_scale == "0"
assert service_annotations.get("run.googleapis.com/ingress") == "internal"
container = template["spec"]["containers"][0]
assert template["spec"]["containerConcurrency"] == 1
assert container["resources"]["limits"] == {"cpu": "1", "memory": "512Mi"}
print(service["status"]["url"])
PY
)
[[ $guard_service_url == https://*.run.app ]] || { printf '%s\n' 'Cost guard did not return its managed HTTPS URL.' >&2; exit 2; }
gcloud run services add-iam-policy-binding "$guard_service" --project="$GCP_PROJECT_ID" \
  --region="$GCP_REGION" --member="serviceAccount:$guard_push_account" \
  --role=roles/run.invoker --quiet
if gcloud pubsub subscriptions describe "$budget_subscription" --project="$GCP_PROJECT_ID" >/dev/null 2>&1; then
  gcloud pubsub subscriptions update "$budget_subscription" --project="$GCP_PROJECT_ID" \
    --push-endpoint="$guard_service_url/" \
    --push-auth-service-account="$guard_push_account" \
    --push-auth-token-audience="$guard_service_url" \
    --ack-deadline=30 --expiration-period=never --quiet
else
  gcloud pubsub subscriptions create "$budget_subscription" --project="$GCP_PROJECT_ID" \
    --topic="$budget_topic" \
    --push-endpoint="$guard_service_url/" \
    --push-auth-service-account="$guard_push_account" \
    --push-auth-token-audience="$guard_service_url" \
    --ack-deadline=30 --expiration-period=never --quiet
fi

environment_values=(
  "DJANGO_ENV=production"
  "DJANGO_DEBUG=false"
  "DJANGO_AUTH_MODE=google"
  "DJANGO_ADMIN_ENABLED=false"
  "DJANGO_ALLOWED_HOSTS=.run.app,.web.app,.firebaseapp.com"
  "DJANGO_CSRF_TRUSTED_ORIGINS=https://$GCP_FIREBASE_SITE.web.app,https://$GCP_FIREBASE_SITE.firebaseapp.com"
  "DJANGO_CORS_ALLOWED_ORIGINS=https://$GCP_FIREBASE_SITE.web.app,https://$GCP_FIREBASE_SITE.firebaseapp.com"
  "DJANGO_TRUST_PROXY=true"
  "DJANGO_PERSISTENCE_BACKEND=firestore"
  "FIRESTORE_DATABASE_MODE=datastore"
  "DJANGO_FILE_STORAGE_BACKEND=gcs"
  "GOOGLE_CLOUD_PROJECT=$GCP_PROJECT_ID"
  "GOOGLE_CLOUD_STORAGE_BUCKET=$GCP_STORAGE_BUCKET"
  "GOOGLE_OAUTH_CLIENT_ID=$GOOGLE_OAUTH_CLIENT_ID"
  "AUDIVERIS_COMMAND=/opt/audiveris/bin/Audiveris"
  "OMR_TIMEOUT_SECONDS=600"
  "OMR_ESTIMATED_SECONDS_PER_PAGE=30"
  "PUBLIC_MAX_SCORES_PER_SESSION=10"
  "PUBLIC_MAX_BYTES_PER_SESSION=52428800"
  "PUBLIC_MAX_SCORES_TOTAL=50"
  "PUBLIC_MAX_BYTES_TOTAL=262144000"
  "API_REQUEST_RATE=10000/hour"
  "UPLOAD_REQUEST_RATE=100/day"
  "OMR_REQUEST_RATE=20/day"
  "OMR_DAILY_LIMIT=20"
)
existing_service_url=$(gcloud run services describe "$GCP_CLOUD_RUN_SERVICE" \
  --project="$GCP_PROJECT_ID" --region="$GCP_REGION" --format='value(status.url)' 2>/dev/null || true)
if [[ $existing_service_url == https://*.run.app ]]; then
  environment_values+=("CLOUD_RUN_PUBLIC_URL=$existing_service_url")
fi
joined_environment=''
for value in "${environment_values[@]}"; do
  joined_environment+="@${value}"
done

gcloud run deploy "$GCP_CLOUD_RUN_SERVICE" \
  --project="$GCP_PROJECT_ID" \
  --region="$GCP_REGION" \
  --image="$immutable_image" \
  --service-account="$GCP_RUNTIME_SERVICE_ACCOUNT" \
  --allow-unauthenticated \
  --ingress=all \
  --execution-environment=gen2 \
  --port=8080 \
  --cpu=1 \
  --memory=4Gi \
  --concurrency=4 \
  --timeout=900 \
  --min=0 \
  --max=1 \
  --no-cpu-boost \
  --set-env-vars="^@^${joined_environment#@}" \
  --set-secrets="DJANGO_SECRET_KEY=$GCP_DJANGO_SECRET:latest" \
  --quiet

service_json="$temporary_dir/service.json"
gcloud run services describe "$GCP_CLOUD_RUN_SERVICE" \
  --project="$GCP_PROJECT_ID" --region="$GCP_REGION" --format=json > "$service_json"
service_url=$(python3 - "$service_json" "$GCP_RUNTIME_SERVICE_ACCOUNT" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    service = json.load(source)
template = service["spec"]["template"]
assert template["spec"]["serviceAccountName"] == sys.argv[2]
service_annotations = service["metadata"].get("annotations", {})
template_annotations = template["metadata"].get("annotations", {})
max_scale = service_annotations.get(
    "run.googleapis.com/maxScale",
    template_annotations.get("autoscaling.knative.dev/maxScale"),
)
min_scale = service_annotations.get(
    "run.googleapis.com/minScale",
    template_annotations.get("autoscaling.knative.dev/minScale", "0"),
)
assert max_scale == "1"
assert min_scale == "0"
containers = template["spec"]["containers"]
assert len(containers) == 1
assert template["spec"]["containerConcurrency"] == 4
assert containers[0]["resources"]["limits"] == {"cpu": "1", "memory": "4Gi"}
print(service["status"]["url"])
PY
)
[[ $service_url == https://*.run.app ]] || { printf '%s\n' 'Cloud Run did not return its managed HTTPS URL.' >&2; exit 2; }

# A first deployment does not have a discoverable service URL until Cloud Run
# creates it. Publish that URL before Firebase exposes the application so the
# browser can bypass Hosting's 60-second proxy timeout only for long OMR jobs.
if [[ $existing_service_url != "$service_url" ]]; then
  gcloud run services update "$GCP_CLOUD_RUN_SERVICE" \
    --project="$GCP_PROJECT_ID" --region="$GCP_REGION" \
    --update-env-vars="CLOUD_RUN_PUBLIC_URL=$service_url" --quiet
fi

health_file="$temporary_dir/health.json"
curl --fail --show-error --silent --retry 8 --retry-all-errors --retry-delay 5 \
  --connect-timeout 10 --max-time 60 "$service_url/api/health/" > "$health_file"
python3 - "$health_file" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as source:
    assert json.load(source) == {"status": "ok", "service": "score-companion-api"}
PY

# The frontend is static Firebase Hosting. The /api rewrite preserves a single
# browser origin for CSRF-protected signed-cookie sessions.
firebase deploy --only hosting --project "$GCP_PROJECT_ID" --non-interactive
public_url="https://$GCP_FIREBASE_SITE.web.app"
curl --fail --show-error --silent --retry 8 --retry-all-errors --retry-delay 5 \
  --connect-timeout 10 --max-time 60 "$public_url/api/health/" > "$health_file"
python3 - "$health_file" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as source:
    assert json.load(source) == {"status": "ok", "service": "score-companion-api"}
PY
curl --fail --show-error --silent --connect-timeout 10 --max-time 60 "$public_url/" | grep -q 'Score Companion'

# This approved deletion occurs only after the revision and public HTTPS checks
# pass. Cloud Run has already imported the immutable image for the revision.
gcloud artifacts docker images delete "$immutable_image" --delete-tags --quiet
immutable_image=''
gcloud artifacts docker images delete "$guard_immutable_image" --delete-tags --quiet
guard_immutable_image=''
printf 'PUBLIC_URL=%s\n' "$public_url" > cloud-run.env
printf 'Release %s verified through Firebase Hosting at %s\n' "$CI_COMMIT_SHA" "$public_url"
