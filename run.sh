#!/usr/bin/env bash
set -euo pipefail

# ── Image ─────────────────────────────────────────────────────────────────────
IMAGE_NAME="killiankopp/ms-geofencing"
IMAGE_TAG="${IMAGE_TAG:-1.0.0}"
CONTAINER_NAME="${CONTAINER_NAME:-geofencing}"

# ── Flux vidéo ────────────────────────────────────────────────────────────────
VIDEO_SOURCE="${VIDEO_SOURCE:-rtsp://10.0.0.136/live2.sdp}"
FRAME_WIDTH="${FRAME_WIDTH:-640}"
FRAME_HEIGHT="${FRAME_HEIGHT:-360}"
TARGET_FPS="${TARGET_FPS:-5}"

# ── Zone de détection ─────────────────────────────────────────────────────────
# Laisser vide = tout le frame
POLYGON="${POLYGON:-}"
MIN_OBJECT_SIZE="${MIN_OBJECT_SIZE:-1000}"

# ── Capture ───────────────────────────────────────────────────────────────────
CAPTURE_INTERVAL="${CAPTURE_INTERVAL:-5}"
CAPTURE_DIR="${CAPTURE_DIR:-/tmp/captures}"
HOST_CAPTURE_DIR="${HOST_CAPTURE_DIR:-$(pwd)/captures}"

# ── Affichage ─────────────────────────────────────────────────────────────────
HEADLESS="${HEADLESS:-true}"
SHOW_VIDEO="${SHOW_VIDEO:-false}"
SHOW_MASK="${SHOW_MASK:-false}"
SHOW_ZONE="${SHOW_ZONE:-true}"
SHOW_INTRUSION="${SHOW_INTRUSION:-true}"

# ── Kafka (optionnel) ─────────────────────────────────────────────────────────
KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS:-kafka-service.kafka.svc.cluster.local:9092}"   # ex: kafka:9092
KAFKA_TOPIC="${KAFKA_TOPIC:-test-ms-geofencing}"                           # ex: geofencing.intrusions
SERVICE_ID="${SERVICE_ID:-${CONTAINER_NAME}}"

# ── Reconnexion ────────────────────────────────────────────────────────────────
RECONNECT_DELAY="${RECONNECT_DELAY:-5}"
RECONNECT_MAX_DELAY="${RECONNECT_MAX_DELAY:-60}"

# ── Préparation ───────────────────────────────────────────────────────────────
mkdir -p "$HOST_CAPTURE_DIR"

# ── Lancement ─────────────────────────────────────────────────────────────────
echo "🚀 Starting container '${CONTAINER_NAME}' (${IMAGE_NAME}:${IMAGE_TAG})"
echo "   📹 VIDEO_SOURCE  : ${VIDEO_SOURCE}"
echo "   📐 Resolution    : ${FRAME_WIDTH}x${FRAME_HEIGHT} @ ${TARGET_FPS} fps"
echo "   🔷 Polygon       : ${POLYGON:-<full frame>}"
echo "   💾 Captures      : ${HOST_CAPTURE_DIR} → ${CAPTURE_DIR}"
echo "   📨 Kafka         : ${KAFKA_BOOTSTRAP_SERVERS:-disabled} ${KAFKA_TOPIC:+→ ${KAFKA_TOPIC}}"
echo ""

docker run --rm -d \
  --name "${CONTAINER_NAME}" \
  --platform linux/amd64 \
  -e VIDEO_SOURCE="${VIDEO_SOURCE}" \
  -e FRAME_WIDTH="${FRAME_WIDTH}" \
  -e FRAME_HEIGHT="${FRAME_HEIGHT}" \
  -e TARGET_FPS="${TARGET_FPS}" \
  -e POLYGON="${POLYGON}" \
  -e MIN_OBJECT_SIZE="${MIN_OBJECT_SIZE}" \
  -e CAPTURE_INTERVAL="${CAPTURE_INTERVAL}" \
  -e CAPTURE_DIR="${CAPTURE_DIR}" \
  -e HEADLESS="${HEADLESS}" \
  -e SHOW_VIDEO="${SHOW_VIDEO}" \
  -e SHOW_MASK="${SHOW_MASK}" \
  -e SHOW_ZONE="${SHOW_ZONE}" \
  -e SHOW_INTRUSION="${SHOW_INTRUSION}" \
  -e KAFKA_BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS}" \
  -e KAFKA_TOPIC="${KAFKA_TOPIC}" \
  -e SERVICE_ID="${SERVICE_ID}" \
  -e RECONNECT_DELAY="${RECONNECT_DELAY}" \
  -e RECONNECT_MAX_DELAY="${RECONNECT_MAX_DELAY}" \
  -v "${HOST_CAPTURE_DIR}:${CAPTURE_DIR}" \
  "${IMAGE_NAME}:${IMAGE_TAG}"



