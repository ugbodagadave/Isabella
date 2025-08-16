from typing import Dict, Any, List
import logging

from integrations.google_sheets_api import GoogleSheetsClient


logger = logging.getLogger(__name__)


def _canon_key(key: str) -> str:
	return (key or "").strip().lower().replace(" ", "_").replace("-", "_")


def _canon_row(row: Dict[str, Any]) -> Dict[str, Any]:
	mapped: Dict[str, Any] = {}
	for k, v in (row or {}).items():
		ck = _canon_key(str(k))
		mapped[ck] = v
	# Normalize common variants to expected keys
	aliases = {
		"date": "date",
		"vendor": "vendor",
		"amount": "amount",
		"category": "category",
		"description": "description",
		"receipt_link": "receipt_link",
		"payment_method": "payment_method",
		"receipt_number": "receipt_number",
		"tax_amount": "tax_amount",
		"location": "location",
		"processed_date": "processed_date",
		"confidence_score": "confidence_score",
	}
	canon: Dict[str, Any] = {}
	for key, target in aliases.items():
		if key in mapped:
			canon[target] = mapped.get(key)
	# Preserve originals too (for any additional fields)
	for k, v in mapped.items():
		if k not in canon:
			canon[k] = v
	return canon


class SheetsManager:
	def __init__(self, client: GoogleSheetsClient) -> None:
		self.client = client

	def append_expense(self, expense: Dict[str, Any]) -> None:
		logger.debug("Appending expense to Google Sheets: vendor=%s amount=%s date=%s", expense.get("vendor"), expense.get("amount"), expense.get("date"))
		self.client.append_row(expense)

	def query_expenses(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
		logger.debug("Querying expenses with filters: %s", list(filters.keys()))
		raw = self.client.query(filters)
		rows = [_canon_row(r) for r in raw]
		logger.info("Fetched %d rows from sheet", len(rows))
		return rows 