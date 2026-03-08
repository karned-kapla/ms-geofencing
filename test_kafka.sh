#!/usr/bin/env bash
# Test de connectivité Kafka depuis l'extérieur du cluster Kubernetes
# Usage: ./test_kafka.sh [bootstrap_servers] [topic]
set -euo pipefail

BOOTSTRAP="${1:-${KAFKA_BOOTSTRAP_SERVERS:-10.0.0.214:9092}}"
TOPIC="${2:-${KAFKA_TOPIC:-test-ms-geofencing}}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Test de connexion Kafka"
echo "   Bootstrap : ${BOOTSTRAP}"
echo "   Topic     : ${TOPIC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

HOST="${BOOTSTRAP%%:*}"
PORT="${BOOTSTRAP##*:}"

# ── 1. TCP ─────────────────────────────────────────────────────────────────────
echo ""
echo "1️⃣  Test TCP vers ${HOST}:${PORT}..."
if nc -zv -w 5 "${HOST}" "${PORT}" 2>&1; then
  echo "✅ Port TCP accessible"
else
  echo "❌ Port TCP inaccessible — vérifie :"
  echo "   - que le Service Kubernetes expose bien Kafka en NodePort ou LoadBalancer"
  echo "   - que l'IP ${HOST} est joignable depuis ta machine"
  echo "   - que le pare-feu autorise le port ${PORT}"
  exit 1
fi

# ── 2. Kafka via kcat ──────────────────────────────────────────────────────────
echo ""
echo "2️⃣  Test Kafka (metadata) via kcat..."
if command -v kcat &>/dev/null || command -v kafkacat &>/dev/null; then
  BIN="$(command -v kcat 2>/dev/null || command -v kafkacat)"
  if "${BIN}" -b "${BOOTSTRAP}" -L -t "${TOPIC}" 2>&1; then
    echo "✅ Kafka répond et le topic '${TOPIC}' est accessible"
  else
    echo "⚠️  Kafka répond mais le topic '${TOPIC}' est peut-être absent"
  fi
else
  echo "⚠️  kcat non installé — installe-le pour un test plus complet :"
  echo "   brew install kcat"
fi

# ── 3. Kafka via Python ────────────────────────────────────────────────────────
echo ""
echo "3️⃣  Test Kafka via Python (kafka-python)..."
python3 - <<PYEOF
import sys
try:
    from kafka import KafkaProducer, KafkaConsumer
    from kafka.errors import KafkaError
except ImportError:
    print("⚠️  kafka-python non installé : pip install kafka-python")
    sys.exit(0)

bootstrap = "${BOOTSTRAP}"
topic     = "${TOPIC}"

# Test producer
try:
    import json
    producer = KafkaProducer(
        bootstrap_servers=bootstrap,
        request_timeout_ms=5000,
        api_version_auto_timeout_ms=5000,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    future = producer.send(topic, value={"test": "ping"})
    record = future.get(timeout=10)
    producer.close()
    print(f"✅ Message envoyé → topic={record.topic} partition={record.partition} offset={record.offset}")
except KafkaError as e:
    print(f"❌ Erreur Kafka : {e}")
    print()
    print("   Pistes :")
    print("   - Le broker annonce peut-être une adresse interne (advertised.listeners)")
    print(f"     → Vérifie que l'IP annoncée par le broker est bien {bootstrap}")
    print("   - Expose Kafka avec un NodePort ou LoadBalancer et configure :")
    print("     advertised.listeners=PLAINTEXT://<IP_EXTERNE>:<PORT>")
    sys.exit(1)
PYEOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Tous les tests sont passés"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


