# ---------- Stage 1: build the static site ----------
FROM node:26-alpine@sha256:c6ad9e9c1d80f6eb607c26b4b0a132ff7a2344fad1c78ea3baa2a7d4c8de6d94 AS build
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
FROM nginxinc/nginx-unprivileged:stable-alpine@sha256:f5116ed4606f3eb015dd4a8e28cb9b351476dc0ad4bc6e9f93b19cec130cdf03

# Apply ALL available Alpine security fixes at build time. Safe because the image
# is pinned to the Alpine 3.24 stable branch, which ships only bug/security fixes.
# Upstream base images lag behind CVE fixes; this keeps shipped images patched
# between Dependabot base-image bumps. Every build is still scanned by the CI gate.
# History: 2026-10-27 targeted patch (brotli, curl); 2026-11-11 expat/musl/zlib CVEs
# -> targeted list replaced with a full upgrade (see troubleshooting log #16).
USER 0
RUN apk upgrade --no-cache
USER 101

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080
