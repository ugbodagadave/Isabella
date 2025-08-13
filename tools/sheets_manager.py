from typing import Dict, Any, List

from integrations.google_sheets_api import GoogleSheetsClient


class SheetsManager:
	def __init__(self, client: GoogleSheetsClient) -> None:
		self.client = client

	def append_expense(self, expense: Dict[str, Any]) -> None:
		self.client.append_row(expense)

	def query_expenses(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
		return self.client.query(filters) 