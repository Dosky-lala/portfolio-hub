# ---------- Stage 1: install dependencies ----------
FROM python:3.14-slim AS builder
WORKDIR /build

# A self-contained virtualenv is easy to copy into the next stage in one piece
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy ONLY requirements first: this layer (and the slow pip install below)
# stays cached until requirements.txt itself changes.
# pip then removes itself from the venv: the app never needs it at runtime.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && pip uninstall -y pip

# ---------- Stage 2: runtime ----------
FROM python:3.14-slim

# PYTHONUNBUFFERED: logs appear immediately in `docker logs` instead of being buffered
# PYTHONDONTWRITEBYTECODE: no .pyc clutter in the container
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Unprivileged user with a fixed UID, and remove the base image's own pip:
# no package manager in the runtime image means an intruder can't install tools
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser \
 && python -m pip uninstall -y pip

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv

# Code stays owned by root: the app user can READ it but not modify it
COPY app ./app

# Numeric UID: Kubernetes can only verify runAsNonRoot with a number, not a name
USER 10001
EXPOSE 8000

# Exec form (JSON array): uvicorn runs as PID 1 and receives SIGTERM directly,
# so `docker stop` shuts it down gracefully instead of force-killing after 10s
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
