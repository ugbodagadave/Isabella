from unittest.mock import MagicMock, patch
import json

from tools.controller import Controller
from tools.text_extractor import TextExtractor
from tools.receipt_processor import ReceiptProcessor
from tools.sheets_manager import SheetsManager


def make_controller(mock_text: str, mock_receipt: dict, existing_rows=None):
	tex = MagicMock(spec=TextExtractor)
	extractor = tex
	extractor.extract.return_value = mock_text

	rp_client = MagicMock()
	rp_client.generate.return_value = json.dumps(mock_receipt)
	rp_client.parse_json.side_effect = lambda t: json.loads(t)
	receipt_processor = ReceiptProcessor(rp_client)

	sheets_client = MagicMock(spec=SheetsManager)
	sheets_client.query_expenses.return_value = existing_rows or []

	controller = Controller(extractor, receipt_processor, sheets_client)
	return controller, extractor, receipt_processor, sheets_client


def test_controller_handles_file_shared_and_appends():
	mock_text = "ACME Total 12.34 on 2024-01-01"
	mock_receipt = {"vendor": "ACME", "amount": 12.34, "date": "2024-01-01", "category": "Office Supplies"}
	controller, extractor, rp, sheets = make_controller(mock_text, mock_receipt)

	result = controller.handle_file_shared({"local_path": "/tmp/rcpt.png", "receipt_link": "http://link"})
	assert result["status"] == "appended"
	sheets.append_expense.assert_called_once()


def test_controller_detects_duplicate():
	existing_rows = [{"vendor": "ACME", "amount": 12.34, "date": "2024-01-01", "category": "Office Supplies"}]
	mock_text = "ACME Total 12.34 on 2024-01-01"
	mock_receipt = {"vendor": "ACME", "amount": 12.34, "date": "2024-01-01", "category": "Office Supplies"}
	controller, extractor, rp, sheets = make_controller(mock_text, mock_receipt, existing_rows=existing_rows)

	result = controller.handle_file_shared({"local_path": "/tmp/rcpt.png"})
	assert result["status"] == "duplicate" 