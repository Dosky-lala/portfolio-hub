# ---------- Stage 1: install dependencies ----------
FROM python:3.14-slim AS builder

# A self-contained virtualenv is easy to copy into the next stage in one piece
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy ONLY requirements first: this layer (and the slow pip install below)
# stays cached until requirements.txt itself changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Stage 2: runtime ----------
FROM python:3.14-slim

# PYTHONUNBUFFERED: logs appear immediately in `docker logs` instead of being buffered
# PYTHONDONTWRITEBYTECODE: no .pyc clutter in the container
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Unprivileged user with a fixed UID (Kubernetes security policies in Ch 2 check for this)
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv

# Code stays owned by root: appuser can READ it but not modify it
COPY app ./app

USER appuser
EXPOSE 8000

# Exec form (JSON array): uvicorn runs as PID 1 and receives SIGTERM directly,
# so `docker stop` shuts it down gracefully instead of force-killing after 10s
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
