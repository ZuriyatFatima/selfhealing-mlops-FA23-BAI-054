# ============================================================
# app.py — Flask Sentiment Analysis API (Unstable / Blue Slot)
# Model: DistilBERT fine-tuned on SST-2 (positive/negative)
# Student: Zuriyat Fatima | FA23-BAI-054
# ============================================================

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from transformers import pipeline

# ─── Logging Setup ───────────────────────────────────────────
# Logs go to /app/logs/api.log (mounted via PVC) AND console
os.makedirs("/app/logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/app/logs/api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ─── Flask App ───────────────────────────────────────────────
app = Flask(__name__)

# ─── Model Identity ──────────────────────────────────────────
# This is the UNSTABLE (blue) model — DistilBERT
# The stable-fallback has model_version = "stable-v0-1C3A"
MODEL_VERSION = "unstable-v1"

# ─── Load DistilBERT ─────────────────────────────────────────
# 'sentiment-analysis' uses distilbert-base-uncased-finetuned-sst-2-english
# This downloads ~250MB on first run — cached after that
logger.info("Loading DistilBERT model... (first run may take 1-2 minutes)")
try:
    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english"
    )
    logger.info("DistilBERT loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    raise

# ─── Confidence Log File ─────────────────────────────────────
# exporter.py reads this file to get the latest confidence score
# Think of it as a sticky note the chef leaves for the inspector
CONFIDENCE_LOG = "/app/logs/confidence.json"

def write_confidence(score: float, label: str, text: str):
    """Write latest prediction confidence to a shared JSON file."""
    data = {
        "confidence": round(score, 4),
        "label": label,
        "text": text[:100],           # truncate long inputs
        "timestamp": datetime.utcnow().isoformat(),
        "model_version": MODEL_VERSION
    }
    with open(CONFIDENCE_LOG, "w") as f:
        json.dump(data, f)

# ─── Routes ──────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    """Health check — Kubernetes liveness probe uses this."""
    return jsonify({
        "status": "healthy",
        "model_version": MODEL_VERSION
    }), 200


@app.route("/predict", methods=["POST"])
def predict():
    """
    Main prediction endpoint.
    Expects JSON: { "text": "your sentence here" }
    Returns:      { "label": "POSITIVE", "confidence": 0.98, "model_version": "..." }
    """
    # --- Validate input ---
    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' field in request body"}), 400

    text = data["text"].strip()
    if not text:
        return jsonify({"error": "Text field cannot be empty"}), 400

    # --- Run prediction ---
    try:
        result = sentiment_pipeline(text)[0]
        label      = result["label"]       # "POSITIVE" or "NEGATIVE"
        confidence = result["score"]       # float between 0.0 and 1.0

        # Write confidence for Prometheus exporter to pick up
        write_confidence(confidence, label, text)

        logger.info(f"Predicted: {label} ({confidence:.4f}) | Text: '{text[:60]}...'")

        return jsonify({
            "label":         label,
            "confidence":    round(confidence, 4),
            "model_version": MODEL_VERSION,
            "text":          text
        }), 200

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({"error": "Prediction failed", "details": str(e)}), 500


@app.route("/metrics-info", methods=["GET"])
def metrics_info():
    """
    Returns the latest confidence reading as JSON.
    (Separate from /metrics which is served by exporter.py on port 8000)
    """
    try:
        with open(CONFIDENCE_LOG, "r") as f:
            return jsonify(json.load(f)), 200
    except FileNotFoundError:
        return jsonify({"confidence": None, "message": "No predictions yet"}), 200


@app.route("/", methods=["GET"])
def index():
    """Simple HTML frontend for manual UI testing (Selenium uses this)."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Sentiment API</title></head>
    <body>
        <h2>Sentiment Analysis API</h2>
        <p>Model: <strong id="model">unstable-v1</strong></p>
        <textarea id="inputText" rows="4" cols="50"
            placeholder="Enter text to analyse..."></textarea><br><br>
        <button onclick="analyse()">Analyse</button>
        <p id="result"></p>

        <script>
        async function analyse() {
            const text = document.getElementById('inputText').value;
            const res  = await fetch('/predict', {
                method:  'POST',
                headers: {'Content-Type': 'application/json'},
                body:    JSON.stringify({text: text})
            });
            const data = await res.json();
            document.getElementById('result').innerText =
                'Label: ' + data.label + ' | Confidence: ' + data.confidence;
        }
        </script>
    </body>
    </html>
    """, 200


# ─── Entry Point ─────────────────────────────────────────────
if __name__ == "__main__":
    # host="0.0.0.0" makes Flask reachable from outside the container
    app.run(host="0.0.0.0", port=5000, debug=False)
