# ── Stage 1: build wheels ──────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ── Stage 2: runtime ───────────────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

# Runtime libs required by OpenCV headless
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for Kubernetes security context
RUN groupadd --gid 1001 appgroup \
 && useradd --uid 1001 --gid appgroup --no-create-home appuser

WORKDIR /app

# Install pre-built wheels — no compiler needed
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links /wheels /wheels/*.whl \
 && rm -rf /wheels

# Application code only — no config files, no test data
COPY core/ core/
COPY main.py .

RUN chown -R appuser:appgroup /app
USER appuser

# ── Environment defaults (override per pod / ConfigMap / Secret) ───────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HEADLESS=true \
    VIDEO_SOURCE=0 \
    FRAME_WIDTH=640 \
    FRAME_HEIGHT=360 \
    TARGET_FPS=5 \
    MIN_OBJECT_SIZE=1000 \
    CAPTURE_INTERVAL=5 \
    CAPTURE_DIR=/tmp/captures \
    POLYGON="" \
    SHOW_VIDEO=false \
    SHOW_MASK=false \
    SHOW_ZONE=true \
    SHOW_INTRUSION=true \
    KAFKA_BOOTSTRAP_SERVERS="" \
    KAFKA_TOPIC="" \
    SERVICE_ID="" \
    RECONNECT_DELAY=5 \
    RECONNECT_MAX_DELAY=60

CMD ["python", "-u", "main.py"]

