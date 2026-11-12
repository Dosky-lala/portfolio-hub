# Portfolio Hub

[![CI](https://github.com/Dosky-lala/portfolio-hub/actions/workflows/ci.yml/badge.svg)](https://github.com/Dosky-lala/portfolio-hub/actions/workflows/ci.yml)

**A full-stack app (FastAPI + React + PostgreSQL) containerized with security-hardened images and shipped through a DevSecOps CI pipeline.**
It tracks my own DevOps learning-in-public portfolio: each chapter of the series and its completion gate.

> **Chapter 1 of 7** in a hands-on DevOps/GitOps series. One app, carried through containers -> Kubernetes -> DevSecOps -> GitOps -> observability -> Terraform on Azure.

---

## Highlights

| | Before | After |
|---|---|---|
| Backend image size | 501 MB | **74.5 MB** (-85%) |
| Frontend image size | 110 MB | **25.7 MB** (-77%) |
| Total, both images | 611 MB, running as root | **100 MB, nothing runs as root** |
| Vulnerabilities (HIGH + CRITICAL) | 471 (17 critical) | **48** (-90%), **0 critical** |
| Fixable HIGH/CRITICAL shipped | n/a | **0**, enforced by a CI gate |
| Cached rebuild | 5m 13s cold | **6.2s** (~50x faster) |
| Full CI run | n/a | **2m 27s** (lint, test, build, scan, smoke test, publish) |
| Regression detection in a drill | n/a | **~30s** after the test job started |

---

## Architecture

```mermaid
flowchart LR
    U([Browser]) -->|"http://127.0.0.1:8080"| N
    subgraph compose ["Docker Compose network (only port 8080 is published)"]
        N["Nginx (frontend)<br/>static React build<br/>non-root, UID 101"]
        A["FastAPI (backend)<br/>non-root, UID 10001<br/>no pip in runtime"]
        D[("PostgreSQL 18<br/>named volume: pgdata")]
        N -->|"/api/* reverse proxy"| A
        A -->|SQL| D
    end
```

- **Nginx** serves the static React build and proxies `/api/*` to the backend, so the browser talks to a **single origin** (no CORS).
- **FastAPI** exposes a CRUD API plus `/api/health`, which returns **503 if the database is unreachable**, so orchestrators can tell "alive" from "useful".
- **PostgreSQL** data lives in a named volume and survives `docker compose down`.
- Only `127.0.0.1:8080` is published. The API (8000) and database (5432) are reachable **only** inside the Compose network.

## Quick start

Requires Docker Engine with Compose v2.

```bash
git clone https://github.com/Dosky-lala/portfolio-hub.git && cd portfolio-hub
cp .env.example .env
sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$(openssl rand -hex 16)/" .env
docker compose up -d --wait
```

Then open **http://localhost:8080**. Interactive API docs: **http://localhost:8080/api/docs**.

```bash
curl -s localhost:8080/api/health      # {"status":"ok","db":"ok"}
docker compose down                    # stop (data kept)
docker compose down -v                 # stop and delete the database volume
```

## CI/CD pipeline

```mermaid
flowchart LR
    L[Lint<br/>Hadolint, Ruff, ESLint] --> B
    T[Test<br/>pytest + Postgres] --> B
    B[Build & scan<br/>backend, frontend<br/>Trivy gate] --> S[Smoke test<br/>full stack via Compose]
    S --> P[Publish to GHCR<br/>main only, tagged by commit SHA]
```

- **Build once, ship what you scanned.** Each image is built once, saved as a file, scanned, smoke-tested, and *that exact file* is published.
- **Images are tagged with the commit SHA**, never `latest`, so every image traces back to the code that produced it.
- **`main` is protected:** changes go through pull requests, and all five checks must pass before merging. Force pushes are blocked.
- **Dependabot** opens weekly PRs for GitHub Actions, pip, npm and base images; each one is tested by the pipeline before merge.

## Security

| Control | How |
|---|---|
| Least-privilege containers | Both images run as numeric non-root UIDs; the backend runtime image contains no package installer |
| Minimal images | Multi-stage builds: compilers, build tools and `node_modules` never ship |
| Vulnerability gate | Trivy fails the build on **fixable** HIGH/CRITICAL findings and reports everything else |
| Continuous patching | Images apply all available OS security updates at build time (Alpine 3.24 / Debian 13 stable branches) |
| Supply chain | GitHub Actions pinned to **full commit SHAs**; base images and CI tool images pinned by **digest** |
| Pipeline privileges | Read-only token by default; only the publish job can write packages; tokens never interpolated into shell commands |
| Secrets | `.env` is git-ignored; CI generates a random database password per run |
| Network exposure | Only the frontend port is published, bound to localhost |
| HTTP hardening | Security headers, `server_tokens off` |

**Gate policy:** fail on fixable HIGH/CRITICAL only. A pipeline that's always red on vulnerabilities nobody can fix yet gets ignored; a gate on what you *can* fix stays meaningful.

**Triage by exposure:** `npm audit` reports moderate findings in build tooling only (`npm audit --omit=dev` is clean). Build tools never reach the shipped image.

## Testing

13 API tests run against a **real PostgreSQL** database (the schema uses Postgres-specific JSONB, so SQLite would be both wrong and insufficient):

```bash
docker run -d --name hub-db-test -e POSTGRES_USER=hub -e POSTGRES_PASSWORD=testpassword \
  -e POSTGRES_DB=hub_test -p 127.0.0.1:5433:5432 --tmpfs /var/lib/postgresql postgres:18-alpine
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
DATABASE_URL="postgresql+psycopg://hub:testpassword@localhost:5433/hub_test" python -m pytest -v
```

A guard refuses to run the suite unless `DATABASE_URL` points at a database with "test" in its name, because the tests drop all tables.

## Lessons learned

- **Digest pinning freezes your packages, not your risk.** A docs-only pull request failed the vulnerability gate because new CVEs were published against unchanged images. The response was a *policy* (apply security updates at build time), not a one-off patch.
- **"Started" isn't "ready".** A 502 right after a rebuild was a race against container startup. `docker compose up --wait` waits for healthchecks.
- **Read the raw configuration.** Five green checks still couldn't unlock a merge: the branch ruleset contained *one* required check named after the whole comma-separated list. The API showed what the UI hid.
- **The error message isn't always the diagnosis.** A "DNS failure" turned out to be ~10-second network latency.
- **Pinning needs an update process.** Pinned versions go stale; Dependabot turns staleness into tested pull requests.
- **Treat runtime upgrades as decisions.** Dependabot proposed Node 24 -> 26 and Python 3.14 -> 3.15. Node 26 was LTS and adopted everywhere; Python 3.15 was rolled back. One version file per runtime (`.nvmrc`, `.python-version`) keeps laptop, CI and Docker in agreement.

Incident write-up: [Validation regression blocked at pull request](docs/postmortems/2026-11-01-chapter-zero-regression.md). Metrics: [docs/metrics.md](docs/metrics.md).

## Repository layout

```
.github/workflows/ci.yml   CI pipeline
.github/dependabot.yml     Automated dependency updates
backend/                   FastAPI app, Dockerfile, tests
frontend/                  React (Vite) app, Nginx config, Dockerfile
compose.yaml               Local stack: db + backend + frontend
docs/                      Metrics, postmortems
```

## Roadmap

| Chapter | Focus | Status |
|---|---|---|
| 1 | Containerize: multi-stage images, Compose, CI with security gates | Done |
| 2 | Kubernetes on kind: manifests, probes, migrations | Next |
| 3 | DevSecOps CI: secret scanning, SAST, SBOMs | Planned |
| 4 | GitOps: Argo CD, Helm, policy as code | Planned |
| 5 | Observability: Prometheus, Grafana, Loki, alerting | Planned |
| 6 | Terraform on Azure: VNet, AKS, Key Vault | Planned |
| 7 | Capstone: signed images, self-healing deployments | Planned |

## About

Built by **Chris Ihetu** as part of a learning-in-public DevOps portfolio.

[Check LinkedIn Profile](https://www.linkedin.com/in/chris-ihetu-68b566236)

Chapter 1 write-up: [docs/chapters/01-containerize.md](docs/chapters/01-containerize.md) · Launch post: [LinkedIn](https://lnkd.in/p/erjeucSq) · Portfolio index: [docs/portfolio-index.md](docs/portfolio-index.md)
