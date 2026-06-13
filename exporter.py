# ============================================================
# exporter.py — Custom Prometheus Metrics Exporter
# Runs on port 8000 | Scrape interval: 15s (set in prometheus.yml)
# Student: Zuriyat Fatima | FA23-BAI-054
# ============================================================

import json
import time
import logging
import os
from prometheus_client import start_http_server, Gauge, Info
from prometheus_client import REGISTRY, PROCESS_COLLECTOR, PLATFORM_COLLECTOR

# ─── Logging Setup ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ─── File path shared with app.py ────────────────────────────
# app.py writes here, exporter.py reads from here
# Like the sticky note analogy — one writes, one reads
CONFIDENCE_LOG = "/app/logs/confidence.json"

# ─── Prometheus Metrics Definition ───────────────────────────
# Gauge = a number that can go up AND down (perfect for confidence)
# Counter = only goes up (e.g., total requests)
# We use Gauge because confidence fluctuates

# Primary metric: the one Prometheus will alert on
sentiment_confidence = Gauge(
    "sentiment_prediction_confidence",       # metric name in Prometheus
    "Latest prediction confidence score from the sentiment model",
    ["model_version", "label"]               # labels let you filter in Grafana
)

# Secondary metrics: useful for the Grafana dashboard
sentiment_prediction_total = Gauge(
    "sentiment_prediction_total",
    "Total number of predictions made (read from log)"
)

sentiment_model_info = Info(
    "sentiment_model",
    "Information about the currently running sentiment model"
)

# Track if the confidence log file exists yet
sentiment_exporter_healthy = Gauge(
    "sentiment_exporter_healthy",
    "1 if exporter can read confidence log, 0 if not"
)

# ─── Core Reading Function ────────────────────────────────────
def read_confidence_log():
    """
    Reads the latest confidence score written by app.py.
    Returns a dict with confidence, label, model_version.
    Returns None if file doesn't exist yet (no predictions made).
    """
    try:
        if not os.path.exists(CONFIDENCE_LOG):
            # No predictions made yet — this is normal on startup
            logger.warning("confidence.json not found yet. Waiting for first prediction...")
            return None

        with open(CONFIDENCE_LOG, "r") as f:
            data = json.load(f)

        # Validate required fields exist
        required = ["confidence", "label", "model_version"]
        if not all(k in data for k in required):
            logger.error(f"confidence.json missing required fields: {data}")
            return None

        return data

    except json.JSONDecodeError as e:
        # File exists but is malformed (can happen if app.py is mid-write)
        logger.error(f"JSON decode error reading confidence log: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error reading confidence log: {e}")
        return None


# ─── Metrics Update Function ──────────────────────────────────
def update_metrics():
    """
    Called every 15 seconds in the main loop.
    Reads confidence.json and updates all Prometheus Gauge values.
    """
    data = read_confidence_log()

    if data is None:
        # No data yet — set confidence to 0 so Prometheus sees SOMETHING
        # A confidence of 0 will immediately trigger the alert — intentional
        # (if the model isn't running, that's a problem worth alerting on)
        sentiment_confidence.labels(
            model_version="unknown",
            label="UNKNOWN"
        ).set(0)
        sentiment_exporter_healthy.set(0)
        logger.info("Set confidence=0 (no log file yet)")
        return

    confidence    = float(data["confidence"])
    label         = data["label"]
    model_version = data["model_version"]

    # ── Update the main confidence gauge ──
    # We reset all label combinations first to avoid stale metrics
    # (e.g., if model_version changes between restarts)
    sentiment_confidence.labels(
        model_version=model_version,
        label=label
    ).set(confidence)

    # ── Update model info ──
    sentiment_model_info.info({
        "version":   model_version,
        "label":     label,
        "timestamp": data.get("timestamp", "unknown")
    })

    # ── Mark exporter as healthy ──
    sentiment_exporter_healthy.set(1)

    logger.info(
        f"Metrics updated | confidence={confidence:.4f} "
        f"label={label} model={model_version}"
    )


# ─── Main Loop ───────────────────────────────────────────────
if __name__ == "__main__":
    # Start the HTTP server on port 8000
    # Prometheus will scrape http://<pod-ip>:8000/metrics
    logger.info("Starting Prometheus exporter on port 8000...")
    start_http_server(8000)
    logger.info("Exporter running. Updating metrics every 15 seconds.")

    # Set initial model info so Prometheus has something from second 0
    sentiment_model_info.info({
        "version":   "distilbert-v1-unstable",
        "label":     "UNKNOWN",
        "timestamp": "startup"
    })

    # ── Scrape loop ──
    # Every 15 seconds: read the log file → update gauges → sleep
    while True:
        try:
            update_metrics()
        except Exception as e:
            # Never crash the exporter — just log and keep going
            logger.error(f"Error in update loop: {e}")
            sentiment_exporter_healthy.set(0)

        time.sleep(15)
