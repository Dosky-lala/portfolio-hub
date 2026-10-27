# ---------- Stage 1: build the static site ----------
FROM node:24-alpine AS build
WORKDIR /app

# Dependency manifests first, so the npm ci layer stays cached until they change
COPY package.json package-lock.json ./

# npm ci (not npm install): installs EXACTLY what package-lock.json says,
# and fails if the lockfile and package.json disagree -> reproducible builds
RUN npm ci

COPY . .
RUN npm run build

# ---------- Stage 2: serve the built files ----------
# nginx-unprivileged runs as a non-root user (UID 101) and listens on 8080 by default
FROM nginxinc/nginx-unprivileged:stable-alpine

# TEMPORARY PATCH (added 2026-10-27): the upstream image ships brotli/curl versions
# with fixed HIGH CVEs (CVE-2026-111497, CVE-2026-92392). Upgrade ONLY these packages,
# then drop straight back to the unprivileged user.
# Remove this block once upstream publishes a rebuilt image (review monthly).
USER 0
RUN apk upgrade --no-cache brotli-libs curl libcurl
USER 101

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080
