#!/bin/sh
set -eu

mkdir -p "$DJANGO_DATA_DIR/media" "$DJANGO_DATA_DIR/static"
if [ -n "${DJANGO_SECRET_KEY_FILE:-}" ]; then
  python -c 'import os, pathlib, secrets; path = pathlib.Path(os.environ["DJANGO_SECRET_KEY_FILE"]); path.exists() or path.write_text(secrets.token_urlsafe(64)); path.chmod(0o600)'
fi
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec "$@"
