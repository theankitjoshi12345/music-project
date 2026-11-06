# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM nginx:stable-alpine AS frontend
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-build /app/frontend/dist/ /usr/share/nginx/html/
EXPOSE 80

FROM ubuntu:24.04 AS backend
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /app/backend

# Use the official installer, including its Java runtime and native libraries.
# Check the release digest before installing anything from the download.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl python3-venv poppler-utils shared-mime-info \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/venv
RUN curl -fsSL --retry 3 -o /tmp/audiveris.deb \
       https://github.com/Audiveris/audiveris/releases/download/5.11.0/Audiveris-5.11.0-ubuntu24.04-x86_64.deb \
    && echo "f20113aaa33b3149ec8d6a09b2a7963360e65fafd92d69389987a85bbc3ec7a3  /tmp/audiveris.deb" | sha256sum -c - \
    && mkdir -p /usr/share/desktop-directories \
    && apt-get update \
    && apt-get install -y --no-install-recommends /tmp/audiveris.deb \
    && test -x /opt/audiveris/bin/Audiveris \
    && rm /tmp/audiveris.deb \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements*.txt ./
RUN pip install --no-cache-dir -r requirements-docker.txt
COPY backend/ ./
COPY docker/entrypoint.sh /usr/local/bin/score-companion-start
COPY THIRD_PARTY_NOTICES.md /app/THIRD_PARTY_NOTICES.md
RUN chmod +x /usr/local/bin/score-companion-start \
    && useradd --create-home --uid 10001 app \
    && mkdir -p /data \
    && chown app:app /data
# Fix display scaling in batch mode so Audiveris skips GTK monitor detection.
ENV JAVA_TOOL_OPTIONS="-Xmx1g -XX:ActiveProcessorCount=2 -Djava.awt.headless=true -Dsun.java2d.uiScale=1"
USER app
RUN /opt/audiveris/bin/Audiveris -help > /dev/null
EXPOSE 8000
ENTRYPOINT ["score-companion-start"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "720", "--access-logfile", "-", "--error-logfile", "-"]

# Production API/OMR image for Cloud Run. Firebase Hosting serves the Vite
# build; Audiveris and Poppler remain inside this same Linux image.
FROM backend AS cloudrun
ENV DJANGO_DATA_DIR=/tmp/score-companion \
    PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 2 --timeout 720 --access-logfile - --error-logfile -"]
