import json
from unittest.mock import MagicMock, patch
from datetime import date

from tools.query_analyzer import QueryAnalyzer
from tools.controller import Controller
from tools.text_extractor import TextExtractor
from tools.receipt_processor import ReceiptProcessor
from tools.sheets_manager import SheetsManager


def test_query_analyzer_parses_json():
	granite = MagicMock()
	granite.generate.return_value = json.dumps({
		"intent": "summary",
		"time_range": {"start_date": None, "end_date": None, "relative": "last_month"},
		"filters": {"categories": ["Meals & Entertainment"], "vendors": None, "min_amount": None, "max_amount": None, "text_search": None},
		"group_by": "none",
		"trend": {"enabled": False, "granularity": "month"},
		"top_n": {"enabled": False, "dimension": "vendor", "limit": 5},
		"compare": {"enabled": False, "baseline": None, "target": None},
		"sort": {"by": "date", "direction": "desc"},
		"output": {"format": "summary", "chart": {"type": None, "dimension": None, "metric": None}},
	})
	granite.parse_json.side_effect = lambda t: json.loads(t)
	qa = QueryAnalyzer(granite)
	result = qa.analyze("How much did we spend on meals last month?")
	assert result["intent"] == "summary"
	assert result["filters"]["categories"] == ["Meals & Entertainment"]
	assert result["time_range"]["relative"] == "last_month"


def test_controller_handle_query_summary_totals():
	# Prepare analyzer
	granite = MagicMock()
	granite.generate.return_value = json.dumps({
		"intent": "summary",
		"time_range": {"start_date": "2024-01-01", "end_date": "2024-01-31", "relative": None},
		"filters": {"categories": ["Office Supplies"], "vendors": None, "min_amount": None, "max_amount": None, "text_search": None},
		"group_by": "none",
		"trend": {"enabled": False, "granularity": "month"},
		"top_n": {"enabled": False, "dimension": "vendor", "limit": 5},
		"compare": {"enabled": False, "baseline": None, "target": None},
		"sort": {"by": "date", "direction": "desc"},
		"output": {"format": "summary", "chart": {"type": None, "dimension": None, "metric": None}},
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
		"intent": "search",
		"time_range": {"start_date": "2024-01-01", "end_date": "2024-12-31", "relative": None},
		"filters": {"vendors": ["ACME"], "categories": None, "min_amount": None, "max_amount": None, "text_search": None},
		"group_by": "none",
		"trend": {"enabled": False, "granularity": "month"},
		"top_n": {"enabled": False, "dimension": "vendor", "limit": 5},
		"compare": {"enabled": False, "baseline": None, "target": None},
		"sort": {"by": "date", "direction": "asc"},
		"output": {"format": "table", "chart": {"type": None, "dimension": None, "metric": None}},
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


def test_controller_period_last_month_normalization():
	granite = MagicMock()
	granite.generate.return_value = json.dumps({
		"intent": "summary",
		"time_range": {"start_date": None, "end_date": None, "relative": "last_month"},
		"filters": {},
		"group_by": "none",
		"trend": {"enabled": False, "granularity": "month"},
		"top_n": {"enabled": False, "dimension": "vendor", "limit": 5},
		"compare": {"enabled": False, "baseline": None, "target": None},
		"sort": {"by": "date", "direction": "desc"},
		"output": {"format": "summary", "chart": {"type": None, "dimension": None, "metric": None}},
	})
	granite.parse_json.side_effect = lambda t: json.loads(t)
	qa = QueryAnalyzer(granite)

	# Freeze today to 2024-02-15, so last_month is Jan 2024
	with patch("tools.controller.date") as mock_date:
		mock_date.today.return_value = date(2024, 2, 15)
		mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

		sheets = MagicMock(spec=SheetsManager)
		sheets.query_expenses.return_value = [
			{"date": "2024-01-10", "category": "Office Supplies", "vendor": "ACME", "amount": 10},
			{"date": "2024-02-01", "category": "Office Supplies", "vendor": "ACME", "amount": 99},
		]

		controller = Controller(text_extractor=MagicMock(spec=TextExtractor), receipt_processor=MagicMock(spec=ReceiptProcessor), sheets_manager=sheets, query_analyzer=qa)
		msg = controller.handle_query("sum last month")
		assert "Summary:" in msg
		assert "10.00" in msg


def test_top_vendors_last_90_days():
	granite = MagicMock()
	granite.generate.return_value = json.dumps({
		"intent": "top_n",
		"time_range": {"start_date": None, "end_date": None, "relative": "last_90_days"},
		"filters": {},
		"group_by": "vendor",
		"trend": {"enabled": False, "granularity": "month"},
		"top_n": {"enabled": True, "dimension": "vendor", "limit": 5},
		"compare": {"enabled": False, "baseline": None, "target": None},
		"sort": {"by": "total", "direction": "desc"},
		"output": {"format": "summary", "chart": {"type": None, "dimension": None, "metric": None}},
	})
	granite.parse_json.side_effect = lambda t: json.loads(t)
	qa = QueryAnalyzer(granite)

	with patch("tools.controller.date") as mock_date:
		mock_date.today.return_value = date(2024, 4, 1)
		mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

		sheets = MagicMock(spec=SheetsManager)
		sheets.query_expenses.return_value = [
			{"date": "2024-03-10", "vendor": "A", "category": "X", "amount": 50},
			{"date": "2024-03-12", "vendor": "B", "category": "X", "amount": 200},
			{"date": "2024-02-01", "vendor": "A", "category": "X", "amount": 25},
			{"date": "2023-12-15", "vendor": "C", "category": "X", "amount": 999},  # outside window
		]

		controller = Controller(text_extractor=MagicMock(spec=TextExtractor), receipt_processor=MagicMock(spec=ReceiptProcessor), sheets_manager=sheets, query_analyzer=qa)
		msg = controller.handle_query("Top 5 vendors last 90 days")
		assert msg.startswith("Summary: Top 5 vendor(s): ")
		assert "B: 200.00" in msg and "A: 75.00" in msg
		assert "C:" not in msg


def test_chart_category_totals_last_month():
	granite = MagicMock()
	granite.generate.return_value = json.dumps({
		"intent": "aggregate",
		"time_range": {"start_date": None, "end_date": None, "relative": "last_month"},
		"filters": {},
		"group_by": "category",
		"trend": {"enabled": True, "granularity": "month"},
		"top_n": {"enabled": False, "dimension": "category", "limit": 5},
		"compare": {"enabled": False, "baseline": None, "target": None},
		"sort": {"by": "total", "direction": "desc"},
		"output": {"format": "chart", "chart": {"type": "bar", "dimension": "category", "metric": "total"}},
	})
	granite.parse_json.side_effect = lambda t: json.loads(t)
	qa = QueryAnalyzer(granite)

	with patch("tools.controller.date") as mock_date:
		mock_date.today.return_value = date(2024, 2, 15)
		mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)

		sheets = MagicMock(spec=SheetsManager)
		sheets.query_expenses.return_value = [
			{"date": "2024-01-10", "vendor": "A", "category": "Groceries", "amount": 10},
			{"date": "2024-01-11", "vendor": "B", "category": "Office Supplies", "amount": 30},
			{"date": "2024-02-02", "vendor": "A", "category": "Groceries", "amount": 5},
		]

		controller = Controller(text_extractor=MagicMock(spec=TextExtractor), receipt_processor=MagicMock(spec=ReceiptProcessor), sheets_manager=sheets, query_analyzer=qa)
		msg = controller.handle_query("Show total spend last month by category as a chart")
		assert msg.startswith("Chart series prepared: ")
		assert "type=bar" in msg and "dimension=category" in msg and "metric=total" in msg


def test_compare_this_month_vs_last_month_for_office_supplies():
	granite = MagicMock()
	granite.generate.return_value = json.dumps({
		"intent": "compare",
		"time_range": {"start_date": None, "end_date": None, "relative": "this_month"},
		"filters": {"categories": ["Office Supplies"]},
		"group_by": "none",
		"trend": {"enabled": False, "granularity": "month"},
		"top_n": {"enabled": False, "dimension": "vendor", "limit": 5},
		"compare": {"enabled": True, "baseline": {"start_date": "2024-01-01", "end_date": "2024-01-31"}, "target": {"start_date": "2024-02-01", "end_date": "2024-02-29"}},
		"sort": {"by": "total", "direction": "desc"},
		"output": {"format": "summary", "chart": {"type": None, "dimension": None, "metric": None}},
	})
	granite.parse_json.side_effect = lambda t: json.loads(t)
	qa = QueryAnalyzer(granite)

	sheets = MagicMock(spec=SheetsManager)
	sheets.query_expenses.return_value = [
		{"date": "2024-01-10", "category": "Office Supplies", "vendor": "ACME", "amount": 10},
		{"date": "2024-01-11", "category": "Office Supplies", "vendor": "PaperCo", "amount": 20},
		{"date": "2024-02-01", "category": "Office Supplies", "vendor": "ACME", "amount": 7},
		{"date": "2024-02-15", "category": "Office Supplies", "vendor": "ACME", "amount": 3},
		{"date": "2024-02-20", "category": "Groceries", "vendor": "Other", "amount": 50},
	]

	controller = Controller(text_extractor=MagicMock(spec=TextExtractor), receipt_processor=MagicMock(spec=ReceiptProcessor), sheets_manager=sheets, query_analyzer=qa)
	msg = controller.handle_query("Compare this month vs last month for office supplies")
	assert msg.startswith("Compare: baseline total 30.00")
	assert "target total 10.00" in msg 