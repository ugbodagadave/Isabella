from tools.sheets_manager import SheetsManager


class DummySheets:
	def __init__(self):
		self.appended = []

	def append_row(self, expense):
		self.appended.append(expense)

	def query(self, filters):
		return self.appended


def test_sheets_manager_basic():
	client = DummySheets()
	sm = SheetsManager(client)  # type: ignore[arg-type]
	sm.append_expense({"vendor": "ACME"})
	rows = sm.query_expenses({})
	assert rows and rows[0]["vendor"] == "ACME" 