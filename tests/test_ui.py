# tests/test_ui.py — Selenium UI Test for Sentiment API
# Function: test_frontend_sentiment (exact name required by spec)
# Element IDs from index.html: text-input, submit-btn, result-output
# Student: Zuriyat Fatima | FA23-BAI-054

import pytest
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:5000")

TEST_TEXT = (
    "The cinematography was breathtaking and the "
    "performances were outstanding"
)


@pytest.fixture(scope="function")
def driver():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,800")

    # Try PATH first, then common snap location
    try:
        drv = webdriver.Chrome(options=opts)
    except Exception:
        svc = Service("/snap/bin/chromium.chromedriver")
        drv = webdriver.Chrome(service=svc, options=opts)

    drv.implicitly_wait(10)
    yield drv
    drv.quit()


def test_frontend_sentiment(driver):
    """
    Opens frontend, types assigned MOVIE test text, clicks submit,
    asserts result-output is non-empty and contains POSITIVE, NEGATIVE,
    or Confidence — using exact element IDs from index.html.
    """
    driver.get(BASE_URL)

    wait = WebDriverWait(driver, 15)

    # Find text-input (exact ID from index.html)
    text_input = wait.until(
        EC.presence_of_element_located((By.ID, "text-input"))
    )
    text_input.clear()
    text_input.send_keys(TEST_TEXT)

    time.sleep(0.5)

    # Click submit-btn (exact ID from index.html)
    submit_btn = driver.find_element(By.ID, "submit-btn")
    submit_btn.click()

    # Wait for result-output to be non-empty (exact ID from index.html)
    result_div = wait.until(
        EC.presence_of_element_located((By.ID, "result-output"))
    )
    wait.until(
        lambda d: d.find_element(By.ID, "result-output").text.strip() != ""
    )

    result_text = result_div.text.strip()

    # Assert non-empty AND contains POSITIVE, NEGATIVE, or Confidence
    assert result_text != "", "result-output was empty"
    assert any(word in result_text.upper() for word in ["POSITIVE", "NEGATIVE", "CONFIDENCE"]), (
        f"Expected POSITIVE, NEGATIVE, or Confidence in result. Got: '{result_text}'"
    )

    print(f"\n✅ UI test passed | Result: '{result_text}'")
