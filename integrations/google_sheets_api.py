from typing import Dict, Any, List
from datetime import datetime
from zoneinfo import ZoneInfo
import json
from pathlib import Path

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

	def _load_default_headers(self) -> List[str]:
		try:
			path = Path(__file__).resolve().parents[1] / "data" / "templates" / "sheets_template.json"
			with open(path, "r", encoding="utf-8") as f:
				data = json.load(f)
			return list(data.get("columns", []))
		except Exception:
			# Fallback minimal headers
			return [
				"Date",
				"Vendor",
				"Amount",
				"Category",
				"Description",
				"Receipt_Link",
				"Payment_Method",
				"Receipt_Number",
				"Tax_Amount",
				"Location",
				"Processed_Date",
				"Confidence_Score",
			]

	@staticmethod
	def _canon(s: str) -> str:
		return (s or "").strip().lower().replace(" ", "_").replace("-", "_")

	def append_row(self, expense: Dict[str, Any]) -> None:
		if self._sheet is None:
			self.connect()

		# Ensure header row exists; if empty, seed from template
		values = self._sheet.get_all_values()
		if not values or (values and not any(values[0])):
			headers = self._load_default_headers()
			self._sheet.update("A1", [headers])
			values = [headers]

		headers = values[0]
		canon_headers = [self._canon(h) for h in headers]

		# Compute processed date now
		try:
			processed_dt = datetime.now(ZoneInfo(self.settings.rules.timezone)).isoformat()
		except Exception:
			processed_dt = datetime.now().isoformat()

		# Map known fields to canonical keys
		field_values: Dict[str, Any] = {
			"date": expense.get("date", ""),
			"vendor": expense.get("vendor", ""),
			"amount": expense.get("amount", ""),
			"category": expense.get("category", ""),
			"description": expense.get("description", ""),
			"receipt_link": expense.get("receipt_link", ""),
			"payment_method": expense.get("payment_method", ""),
			"receipt_number": expense.get("receipt_number", ""),
			"tax_amount": expense.get("tax_amount", ""),
			"location": expense.get("location", ""),
			"processed_date": processed_dt,
			"confidence_score": expense.get("confidence", ""),
		}

		row: List[Any] = []
		for key in canon_headers:
			row.append(field_values.get(key, ""))

		self._sheet.append_row(row, value_input_option="USER_ENTERED")

	def query(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
		if self._sheet is None:
			self.connect()
		# Prefer get_all_records; if header row has duplicates, fall back safely
		try:
			records = self._sheet.get_all_records()
			return records
		except Exception:
			values = self._sheet.get_all_values()
			if not values:
				return []
			headers = values[0]
			# De-duplicate headers by suffixing duplicates
			seen: Dict[str, int] = {}
			unique_headers: List[str] = []
			for h in headers:
				key = str(h or "").strip()
				count = seen.get(key, 0) + 1
				seen[key] = count
				unique_headers.append(key if count == 1 else f"{key}_{count}")
			rows = values[1:]
			records: List[Dict[str, Any]] = []
			for row in rows:
				record: Dict[str, Any] = {}
				for i, col in enumerate(unique_headers):
					record[col] = row[i] if i < len(row) else ""
				records.append(record)
			return records 