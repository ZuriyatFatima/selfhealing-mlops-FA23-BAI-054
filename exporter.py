# exporter.py — Custom Prometheus Metrics Exporter
# Runs on EC2 host (not inside Kubernetes)
# Polls the app via NodePort 32500 every 5s
# Exposes metric: prediction_confidence_score on port 8000
# Student: Zuriyat Fatima | FA23-BAI-054

import time
import logging
import requests
from prometheus_client import start_http_server, Gauge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ── EXACT metric name required by spec and grading script ──
prediction_confidence_score = Gauge(
    "prediction_confidence_score",
    "Latest prediction confidence score from the sentiment API"
)

# Poll the app via NodePort — this is how exporter reaches the pod
APP_URL = "http://192.168.49.2:32500/api/latest-confidence"
POLL_INTERVAL = 5   # seconds — spec says every 5s

if __name__ == "__main__":
    logger.info("Starting Prometheus exporter on port 8000...")
    start_http_server(8000)
    logger.info(f"Exporter running. Polling {APP_URL} every {POLL_INTERVAL}s.")

    while True:
        try:
            r = requests.get(APP_URL, timeout=3)
            if r.status_code == 200:
                confidence = float(r.json().get("confidence", 1.0))
            else:
                confidence = 1.0
        except Exception as e:
            # If endpoint unreachable, default to 1.0 (spec requirement)
            logger.warning(f"Could not reach app: {e} — defaulting to 1.0")
            confidence = 1.0

        prediction_confidence_score.set(confidence)
        logger.info(f"confidence={confidence:.4f}")

        time.sleep(POLL_INTERVAL)
