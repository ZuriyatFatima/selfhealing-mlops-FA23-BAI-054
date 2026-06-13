# tests/test_api.py — PyTest Unit Tests for Sentiment API
# Exact function names required by spec — do not rename
# Runs against live container at API_BASE_URL (set by Jenkins)
# Student: Zuriyat Fatima | FA23-BAI-054

import pytest
import requests
import os

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:5000")


def test_health_endpoint():
    """GET /health -> HTTP 200; 'status':'healthy' and key 'model_version' present"""
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "healthy"
    assert "model_version" in data


def test_predict_returns_label_and_confidence():
    """POST /predict -> HTTP 200; label in [POSITIVE,NEGATIVE]; 0<=confidence<=1; 'model_version' present"""
    r = requests.post(
        f"{BASE_URL}/predict",
        json={"text": "The cinematography was breathtaking and the performances were outstanding"}
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("label") in ["POSITIVE", "NEGATIVE"]
    assert 0 <= data.get("confidence", -1) <= 1
    assert "model_version" in data


def test_predict_negative_text():
    """POST /predict with negative text -> HTTP 200"""
    r = requests.post(
        f"{BASE_URL}/predict",
        json={"text": "This film was absolutely terrible and a complete waste of time"}
    )
    assert r.status_code == 200


def test_health_returns_model_version_unstable():
    """GET /health -> model_version == 'unstable-v1' exactly"""
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("model_version") == "unstable-v1"
