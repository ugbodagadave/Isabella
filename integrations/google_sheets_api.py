from typing import Dict, Any, List

import gspread
from google.oauth2.service_account import Credentials

from config.settings import load_settings


class GoogleSheetsClient:
	def __init__(self) -> None:
		self.settings = load_settings()
		self._gc = None
		self._sheet = None

	def connect(self) -> None:
		creds = Credentials.from_service_account_file(
			self.settings.google_sheets.credentials_path,
			scopes=[
				"https://www.googleapis.com/auth/spreadsheets",
				"https://www.googleapis.com/auth/drive.file",
			],
		)
		self._gc = gspread.authorize(creds)
		ss = self._gc.open_by_key(self.settings.google_sheets.spreadsheet_id)
		self._sheet = ss.worksheet(self.settings.google_sheets.worksheet_name)

	def append_row(self, expense: Dict[str, Any]) -> None:
		if self._sheet is None:
			self.connect()
		# Expect columns to be pre-configured; map dict to row order
		row = [
			expense.get("date", ""),
			expense.get("vendor", ""),
			expense.get("amount", ""),
			expense.get("category", ""),
			expense.get("description", ""),
			expense.get("receipt_link", ""),
		]
		self._sheet.append_row(row, value_input_option="USER_ENTERED")

	def query(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
		if self._sheet is None:
			self.connect()
		# Placeholder: real implementation would filter on the client or read and filter locally
		records = self._sheet.get_all_records()
		return records 