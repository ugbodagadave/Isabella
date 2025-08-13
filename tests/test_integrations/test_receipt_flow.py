from unittest.mock import patch, MagicMock
import json

from tools.text_extractor import TextExtractor
from tools.receipt_processor import ReceiptProcessor
from tools.sheets_manager import SheetsManager


def test_end_to_end_mocked_flow():
	# Mock OCR to return synthetic text
	with patch("tools.text_extractor.pytesseract.image_to_string", return_value="ACME Store Total 12.34 on 2024-01-01"), \
		 patch("tools.text_extractor.Image.open"):
		ocr = TextExtractor()
		text = ocr.extract_from_image("/path/to/receipt.png")

	# Mock Granite generate/parse_json to return valid receipt JSON
	granite = MagicMock()
	granite.generate.return_value = json.dumps({
		"vendor": "ACME",
		"amount": 12.34,
		"date": "2024-01-01",
		"category": "Office Supplies",
		"description": "Pens"
	})
	granite.parse_json.side_effect = lambda t: json.loads(t)

	rp = ReceiptProcessor(granite)
	receipt = rp.process(text)
	assert receipt["vendor"] == "ACME"

	# Mock Sheets append
	with patch("integrations.google_sheets_api.Credentials.from_service_account_file", return_value=object()), \
		 patch("integrations.google_sheets_api.gspread.authorize") as mock_auth:
		fake_ws = MagicMock()
		fake_ss = MagicMock()
		fake_gc = MagicMock()
		fake_gc.open_by_key.return_value = fake_ss
		fake_ss.worksheet.return_value = fake_ws
		mock_auth.return_value = fake_gc

		from integrations.google_sheets_api import GoogleSheetsClient

		client = GoogleSheetsClient()
		sheets = SheetsManager(client)
		sheets.append_expense({**receipt, "receipt_link": "http://link"})

		fake_ws.append_row.assert_called_once() 