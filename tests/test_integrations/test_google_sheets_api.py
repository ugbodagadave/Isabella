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
	fake_gc.create = MagicMock(return_value={"spreadsheetId": "abc"})

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
			"payment_method": "Card",
			"receipt_number": "R1",
			"tax_amount": 0.67,
			"location": "NYC",
			"confidence": 95,
		}
		client.append_row(expense)

		fake_worksheet.append_row.assert_called_once()
		args, kwargs = fake_worksheet.append_row.call_args
		row = args[0]
		# Processed date is dynamic at index -2; assert fixed prefix and suffix
		assert row[:6] == ["2024-01-01", "ACME", 12.34, "Office Supplies", "pens", "http://link"]
		assert row[6:10] == ["Card", "R1", 0.67, "NYC"]
		assert row[-1] == 95

		# Query returns records from worksheet
		records = client.query({})
		assert records == fake_records

		# Create spreadsheet helper
		created = client.create_spreadsheet("Title")
		assert created == {"spreadsheetId": "abc"}
		fake_gc.create.assert_called_once_with("Title")

		# Open worksheet helper
		ws = client.open_worksheet("Expenses")
		assert ws is fake_worksheet 