import json
from unittest.mock import MagicMock

from tools.query_analyzer import QueryAnalyzer
from tools.controller import Controller
from tools.text_extractor import TextExtractor
from tools.receipt_processor import ReceiptProcessor
from tools.sheets_manager import SheetsManager


def test_query_analyzer_parses_json():
	granite = MagicMock()
	granite.generate.return_value = json.dumps({
		"query_type": "summary",
		"time_range": {"start_date": None, "end_date": None, "period": "last_month"},
		"filters": {"categories": ["Meals & Entertainment"], "vendors": None, "min_amount": None, "max_amount": None},
		"response_format": "summary",
	})
	granite.parse_json.side_effect = lambda t: json.loads(t)
	qa = QueryAnalyzer(granite)
	result = qa.analyze("How much did we spend on meals last month?")
	assert result["query_type"] == "summary"
	assert result["filters"]["categories"] == ["Meals & Entertainment"]


def test_controller_handle_query_summary_totals():
	# Prepare analyzer
	granite = MagicMock()
	granite.generate.return_value = json.dumps({
		"query_type": "summary",
		"time_range": {"start_date": None, "end_date": None, "period": None},
		"filters": {"categories": ["Office Supplies"]},
		"response_format": "summary",
	})
	granite.parse_json.side_effect = lambda t: json.loads(t)
	qa = QueryAnalyzer(granite)

	# Prepare sheets rows
	sheets = MagicMock(spec=SheetsManager)
	sheets.query_expenses.return_value = [
		{"category": "Office Supplies", "amount": 10},
		{"category": "Office Supplies", "amount": 5.5},
		{"category": "Travel & Transportation", "amount": 20},
	]

	controller = Controller(text_extractor=MagicMock(spec=TextExtractor), receipt_processor=MagicMock(spec=ReceiptProcessor), sheets_manager=sheets, query_analyzer=qa)
	msg = controller.handle_query("sum office supplies")
	assert "Summary:" in msg
	assert "15.50" in msg 