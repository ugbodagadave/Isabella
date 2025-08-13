from unittest.mock import patch, MagicMock

from integrations.google_sheets_api import GoogleSheetsClient


def test_google_sheets_client_append_and_query():
	fake_records = [{"date": "2024-01-01", "vendor": "ACME", "amount": 12.34, "category": "Office Supplies", "description": "pens", "receipt_link": "http://link"}]

	# Prepare fakes
	fake_worksheet = MagicMock()
	fake_worksheet.append_row = MagicMock()
	fake_worksheet.get_all_records = MagicMock(return_value=fake_records)

	fake_ss = MagicMock()
	fake_ss.worksheet = MagicMock(return_value=fake_worksheet)

	fake_gc = MagicMock()
	fake_gc.open_by_key = MagicMock(return_value=fake_ss)

	with patch("integrations.google_sheets_api.Credentials.from_service_account_file", return_value=object()) as mock_creds, \
		 patch("integrations.google_sheets_api.gspread.authorize", return_value=fake_gc) as mock_auth:
		client = GoogleSheetsClient()

		# Append expense maps to row order
		expense = {
			"date": "2024-01-01",
			"vendor": "ACME",
			"amount": 12.34,
			"category": "Office Supplies",
			"description": "pens",
			"receipt_link": "http://link",
		}
		client.append_row(expense)

		fake_worksheet.append_row.assert_called_once()
		args, kwargs = fake_worksheet.append_row.call_args
		row = args[0]
		assert row == ["2024-01-01", "ACME", 12.34, "Office Supplies", "pens", "http://link"]

		# Query returns records from worksheet
		records = client.query({})
		assert records == fake_records 