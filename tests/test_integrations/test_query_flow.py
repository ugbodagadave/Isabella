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
		"time_range": {"start_date": "2024-01-01", "end_date": "2024-01-31", "period": None},
		"filters": {"categories": ["Office Supplies"]},
		"response_format": "summary",
	})
	granite.parse_json.side_effect = lambda t: json.loads(t)
	qa = QueryAnalyzer(granite)

	# Prepare sheets rows spanning date range
	sheets = MagicMock(spec=SheetsManager)
	sheets.query_expenses.return_value = [
		{"date": "2023-12-31", "category": "Office Supplies", "vendor": "ACME", "amount": 100},
		{"date": "2024-01-10", "category": "Office Supplies", "vendor": "ACME", "amount": 10},
		{"date": "2024-01-11", "category": "Office Supplies", "vendor": "PaperCo", "amount": 5.5},
		{"date": "2024-02-01", "category": "Office Supplies", "vendor": "ACME", "amount": 20},
	]

	controller = Controller(text_extractor=MagicMock(spec=TextExtractor), receipt_processor=MagicMock(spec=ReceiptProcessor), sheets_manager=sheets, query_analyzer=qa)
	msg = controller.handle_query("sum office supplies jan 2024")
	assert "Summary:" in msg
	assert "15.50" in msg
	assert "ACME: 10.00" in msg and "PaperCo: 5.50" in msg


def test_controller_handle_query_table_search():
	granite = MagicMock()
	granite.generate.return_value = json.dumps({
		"query_type": "search",
		"time_range": {"start_date": "2024-01-01", "end_date": "2024-12-31", "period": None},
		"filters": {"vendors": ["ACME"]},
		"response_format": "table",
	})
	granite.parse_json.side_effect = lambda t: json.loads(t)
	qa = QueryAnalyzer(granite)

	sheets = MagicMock(spec=SheetsManager)
	sheets.query_expenses.return_value = [
		{"date": "2024-01-10", "category": "Office Supplies", "vendor": "ACME", "amount": 10},
		{"date": "2024-04-05", "category": "Travel & Transportation", "vendor": "ACME", "amount": 25},
		{"date": "2024-01-11", "category": "Office Supplies", "vendor": "Other", "amount": 5.5},
	]

	controller = Controller(text_extractor=MagicMock(spec=TextExtractor), receipt_processor=MagicMock(spec=ReceiptProcessor), sheets_manager=sheets, query_analyzer=qa)
	table = controller.handle_query("list acme this year")
	assert table.splitlines()[0] == "Date | Vendor | Amount | Category"
	assert "2024-01-10 | ACME | 10.00 | Office Supplies" in table
	assert "2024-04-05 | ACME | 25.00 | Travel & Transportation" in table
	# Should not include vendor Other
	assert "Other" not in table 