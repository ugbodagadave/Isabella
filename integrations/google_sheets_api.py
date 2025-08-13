from typing import Dict, Any, List
from datetime import datetime
from zoneinfo import ZoneInfo

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

	def create_spreadsheet(self, title: str) -> Any:
		if self._gc is None:
			self.connect()
		return self._gc.create(title)

	def open_worksheet(self, worksheet_name: str) -> Any:
		if self._gc is None:
			self.connect()
		ss = self._gc.open_by_key(self.settings.google_sheets.spreadsheet_id)
		return ss.worksheet(worksheet_name)

	def append_row(self, expense: Dict[str, Any]) -> None:
		if self._sheet is None:
			self.connect()
		# Map to template columns order (see data/templates/sheets_template.json)
		try:
			processed_dt = datetime.now(ZoneInfo(self.settings.rules.timezone)).isoformat()
		except Exception:
			processed_dt = datetime.now().isoformat()
		row = [
			expense.get("date", ""),
			expense.get("vendor", ""),
			expense.get("amount", ""),
			expense.get("category", ""),
			expense.get("description", ""),
			expense.get("receipt_link", ""),
			expense.get("payment_method", ""),
			expense.get("receipt_number", ""),
			expense.get("tax_amount", ""),
			expense.get("location", ""),
			processed_dt,
			expense.get("confidence", ""),
		]
		self._sheet.append_row(row, value_input_option="USER_ENTERED")

	def query(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
		if self._sheet is None:
			self.connect()
		# Placeholder: real implementation would filter on the client or read and filter locally
		records = self._sheet.get_all_records()
		return records 