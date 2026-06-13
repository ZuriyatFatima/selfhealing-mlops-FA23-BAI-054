# Dockerfile — Sentiment Analysis API (CPU-optimized)
FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
# Install torch CPU-only first (saves ~1.5GB vs default CUDA build)
RUN pip install --no-cache-dir torch==2.3.0 --index-url https://download.pytorch.org/whl/cpu
# Install remaining dependencies
RUN pip install --no-cache-dir \
    flask==3.0.3 \
    transformers==4.41.2 \
    prometheus-client==0.20.0 \
    requests==2.32.3 \
    pytest==8.2.2 \
    selenium==4.21.0
# Pre-download DistilBERT model into image layer (prevents runtime download timeout)
RUN python3 -c "from transformers import pipeline; pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')"
COPY app.py .
COPY exporter.py .
COPY templates/ templates/
RUN mkdir -p /app/logs
EXPOSE 5000 8000
CMD ["python", "app.py"]
