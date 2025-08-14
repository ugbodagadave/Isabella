import os
import tempfile
import requests
from pathlib import Path
from urllib.parse import urlparse

import pytest

from config.settings import load_settings
from tools.text_extractor import TextExtractor
from models.granite_client import GraniteClient
from tools.receipt_processor import ReceiptProcessor
from integrations.google_sheets_api import GoogleSheetsClient
from integrations.slack_api import SlackApi


pytestmark = pytest.mark.e2e


def _slack_file_id_from_url(url: str) -> str:
	# Slack file URL format: https://workspace.slack.com/files/<user_id>/<file_id>/<name>
	try:
		parts = urlparse(url).path.strip("/").split("/")
		return parts[2] if len(parts) >= 3 else ""
	except Exception:
		return ""


def _download_with_session(url: str, headers: dict) -> requests.Response:
	s = requests.Session()
	s.headers.update(headers)
	r = s.get(url, allow_redirects=True, timeout=60)
	r.raise_for_status()
	return r


def _choose_suffix(resp: requests.Response, fallback_from_url: str) -> str:
	ct = (resp.headers.get("Content-Type") or "").lower()
	content = resp.content
	if b"%PDF" in content[:1024] or "pdf" in ct:
		return ".pdf"
	# Try to infer from URL
	suffix = Path(fallback_from_url).suffix
	if suffix:
		return suffix
	return ".png"


def _download_receipt(path_or_url: str) -> str:
	if not path_or_url.lower().startswith("http"):
		return path_or_url

	headers = {}
	url = path_or_url
	if "slack.com/files" in path_or_url and os.getenv("SLACK_BOT_TOKEN"):
		file_id = _slack_file_id_from_url(path_or_url)
		if file_id:
			try:
				slack = SlackApi(bot_token=os.getenv("SLACK_BOT_TOKEN", ""))
				direct = slack.file_download_url(file_id)
				if direct:
					url = direct
			except Exception:
				pass
		headers["Authorization"] = f"Bearer {os.getenv('SLACK_BOT_TOKEN')}"

	try:
		resp = _download_with_session(url, headers)
	except Exception:
		resp = requests.get(url, headers=headers, timeout=60)
		resp.raise_for_status()

	suffix = _choose_suffix(resp, path_or_url)
	fd, tmp = tempfile.mkstemp(suffix=suffix)
	with os.fdopen(fd, "wb") as f:
		f.write(resp.content)
	return tmp


def test_live_e2e_receipt_to_sheets_and_slack():
	settings = load_settings()
	# Required inputs
	receipt_path = os.getenv("E2E_RECEIPT_PATH") or os.getenv("E2E_RECEIPT_URL")
	assert receipt_path, "Provide E2E_RECEIPT_PATH or E2E_RECEIPT_URL"
	assert settings.watsonx.api_key and settings.watsonx.project_id, "Watsonx credentials required"
	assert settings.google_sheets.credentials_path and settings.google_sheets.spreadsheet_id, "Google Sheets env required"
	assert settings.ocr.tesseract_cmd, "TESSERACT_CMD must be set for OCR"

	receipt_path = _download_receipt(receipt_path)

	# OCR
	extractor = TextExtractor(tesseract_cmd=settings.ocr.tesseract_cmd or None, lang=settings.ocr.tesseract_lang)
	text = extractor.extract(receipt_path)
	assert text and len(text) > 5

	# Granite
	granite = GraniteClient()
	processor = ReceiptProcessor(granite)
	receipt = processor.process(text)
	# Validate essential fields
	assert isinstance(receipt.get("vendor"), str) and receipt.get("vendor").strip()
	assert isinstance(receipt.get("date"), str) and len(receipt.get("date")) == 10
	assert isinstance(receipt.get("amount"), (int, float))

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
	msg = "✅ Your receipt has been added to Google Sheets"
	slack.post_message(channel=channel, text=msg)

	# Verify by reading back records and searching for marker
	records = client.query({})
	found = any(any(str(v).strip() == "E2E_TEST" for v in row.values()) for row in records)
	assert found, "Appended E2E_TEST row not found in sheet records" 