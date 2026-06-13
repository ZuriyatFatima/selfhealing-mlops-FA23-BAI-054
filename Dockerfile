# ============================================================
# Dockerfile — Sentiment Analysis API
# Base image: Python 3.10 slim (small, fast, production-ready)
# ============================================================

FROM python:3.10-slim

# --- Set working directory inside the container ---
# Everything we do from here happens inside /app
WORKDIR /app

# --- Install system dependencies first ---
# We do this before pip installs so Docker can cache this layer
# (If only your Python code changes, Docker won't re-run apt-get)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# --- Copy requirements first (Docker layer caching trick) ---
# If requirements.txt hasn't changed, Docker skips the pip install step
COPY requirements.txt .

# --- Install Python dependencies ---
RUN pip install --no-cache-dir -r requirements.txt

# --- Copy the rest of the application code ---
COPY app.py .
COPY exporter.py .

# --- Create log directory (used by the PVC mount later) ---
RUN mkdir -p /app/logs

# --- Expose ports ---
# 5000: Flask API
# 8000: Prometheus exporter metrics endpoint
EXPOSE 5000 8000

# --- Start command ---
# Runs both app.py (Flask) and exporter.py (metrics) together
# using a shell script approach
CMD sh -c "python exporter.py & python app.py"
