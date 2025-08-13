from typing import Dict, Any, List
import logging

from integrations.google_sheets_api import GoogleSheetsClient


logger = logging.getLogger(__name__)


class SheetsManager:
	def __init__(self, client: GoogleSheetsClient) -> None:
		self.client = client

	def append_expense(self, expense: Dict[str, Any]) -> None:
		logger.debug("Appending expense to Google Sheets: vendor=%s amount=%s date=%s", expense.get("vendor"), expense.get("amount"), expense.get("date"))
		self.client.append_row(expense)

	def query_expenses(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
		logger.debug("Querying expenses with filters: %s", list(filters.keys()))
		return self.client.query(filters) 