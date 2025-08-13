import os
import tempfile
import requests
from pathlib import Path

import pytest

from config.settings import load_settings
from tools.text_extractor import TextExtractor
from models.granite_client import GraniteClient
from tools.receipt_processor import ReceiptProcessor
from integrations.google_sheets_api import GoogleSheetsClient
from integrations.slack_api import SlackApi


pytestmark = pytest.mark.e2e


def _download_if_url(path_or_url: str) -> str:
	if path_or_url.lower().startswith("http"):
		headers = {}
		if "slack.com" in path_or_url and os.getenv("SLACK_BOT_TOKEN"):
			headers["Authorization"] = f"Bearer {os.getenv('SLACK_BOT_TOKEN')}"
		r = requests.get(path_or_url, headers=headers, timeout=60)
		r.raise_for_status()
		suffix = Path(path_or_url).suffix or ".png"
		fd, tmp = tempfile.mkstemp(suffix=suffix)
		with os.fdopen(fd, "wb") as f:
			f.write(r.content)
		return tmp
	return path_or_url


def test_live_e2e_receipt_to_sheets_and_slack():
	settings = load_settings()
	# Required inputs
	receipt_path = os.getenv("E2E_RECEIPT_PATH") or os.getenv("E2E_RECEIPT_URL")
	assert receipt_path, "Provide E2E_RECEIPT_PATH or E2E_RECEIPT_URL"
	assert settings.watsonx.api_key and settings.watsonx.project_id, "Watsonx credentials required"
	assert settings.google_sheets.credentials_path and settings.google_sheets.spreadsheet_id, "Google Sheets env required"
	assert settings.ocr.tesseract_cmd, "TESSERACT_CMD must be set for OCR"

	receipt_path = _download_if_url(receipt_path)

	# OCR
	extractor = TextExtractor(tesseract_cmd=settings.ocr.tesseract_cmd or None, lang=settings.ocr.tesseract_lang)
	text = extractor.extract(receipt_path)
	assert text and len(text) > 5

	# Granite
	granite = GraniteClient()
	processor = ReceiptProcessor(granite)
	receipt = processor.process(text)
	assert receipt.get("vendor") and receipt.get("amount") and receipt.get("date")

	# Append to Sheets (mark description for verification)
	client = GoogleSheetsClient()
	expense = {
		"date": receipt.get("date"),
		"vendor": receipt.get("vendor"),
		"amount": receipt.get("amount"),
		"category": receipt.get("category", "Other Business Expenses"),
		"description": "E2E_TEST",
		"receipt_link": os.getenv("E2E_RECEIPT_URL", ""),
	}
	client.append_row(expense)

	# Slack confirmation message
	channel = os.getenv("SLACK_CHANNEL_ID")
	assert channel, "SLACK_CHANNEL_ID must be set to post confirmation"
	slack = SlackApi(bot_token=os.getenv("SLACK_BOT_TOKEN", ""))
	msg = f"Processed receipt: vendor={expense['vendor']} amount={expense['amount']} date={expense['date']}"
	slack.post_message(channel=channel, text=msg)

	# Verify by reading back records and searching for marker
	records = client.query({})
	found = any(any(str(v).strip() == "E2E_TEST" for v in row.values()) for row in records)
	assert found, "Appended E2E_TEST row not found in sheet records" 