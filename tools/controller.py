from __future__ import annotations

from typing import Any, Dict, Optional, List
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta

from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import load_settings
from tools.text_extractor import TextExtractor
from tools.receipt_processor import ReceiptProcessor
from tools.sheets_manager import SheetsManager
from tools.query_analyzer import QueryAnalyzer


logger = logging.getLogger(__name__)


class Controller:
	def __init__(self, text_extractor: TextExtractor, receipt_processor: ReceiptProcessor, sheets_manager: SheetsManager, query_analyzer: Optional[QueryAnalyzer] = None) -> None:
		self.text_extractor = text_extractor
		self.receipt_processor = receipt_processor
		self.sheets = sheets_manager
		self.settings = load_settings()
		self.query_analyzer = query_analyzer

	def handle_query(self, text: str) -> str:
		if not self.query_analyzer:
			return f"Received query: {text}"
		analysis = self.query_analyzer.analyze(text)
		rows = self.sheets.query_expenses({})
		filtered = self._apply_filters(rows, analysis.get("filters", {}), analysis.get("time_range") or {})
		query_type = analysis.get("query_type", "summary")
		response_format = analysis.get("response_format", "summary")
		if query_type == "summary":
			total = sum(float(r.get("amount", 0) or 0) for r in filtered)
			count = len(filtered)
			vendor_totals: Dict[str, float] = defaultdict(float)
			for r in filtered:
				vendor_totals[str(r.get("vendor", "Unknown"))] += float(r.get("amount", 0) or 0)
			limit = max(1, int(self.settings.rules.top_vendors_limit or 5))
			top_vendors = sorted(vendor_totals.items(), key=lambda kv: kv[1], reverse=True)[:limit]
			vendors_str = "; ".join(f"{v}: {amt:.2f}" for v, amt in top_vendors) if top_vendors else "None"
			return f"Summary: {count} expenses totaling {total:.2f}. Vendors: {vendors_str}"
		elif query_type == "search" and response_format in {"table", "detailed"}:
			return self._render_table(filtered)
		else:
			return f"Found {len(filtered)} matching expenses"

	def _render_table(self, rows: List[Dict[str, Any]]) -> str:
		headers = ["Date", "Vendor", "Amount", "Category"]
		lines = [" | ".join(headers)]
		for r in rows:
			lines.append(" | ".join([
				str(r.get("date", "")),
				str(r.get("vendor", "")),
				f"{float(r.get('amount', 0) or 0):.2f}",
				str(r.get("category", "")),
			]))
		return "\n".join(lines)

	def _normalize_period(self, time_range: Dict[str, Any]) -> Dict[str, Any]:
		period = (time_range or {}).get("period")
		if not period:
			return time_range or {}
		today = date.today()
		if period == "last_month":
			first_this_month = today.replace(day=1)
			last_month_end = first_this_month - timedelta(days=1)
			last_month_start = last_month_end.replace(day=1)
			return {"start_date": last_month_start.strftime("%Y-%m-%d"), "end_date": last_month_end.strftime("%Y-%m-%d"), "period": period}
		if period == "this_month":
			first_this_month = today.replace(day=1)
			return {"start_date": first_this_month.strftime("%Y-%m-%d"), "end_date": today.strftime("%Y-%m-%d"), "period": period}
		if period == "this_year":
			first_this_year = today.replace(month=1, day=1)
			return {"start_date": first_this_year.strftime("%Y-%m-%d"), "end_date": today.strftime("%Y-%m-%d"), "period": period}
		return time_range or {}

	def _apply_filters(self, rows: List[Dict[str, Any]], filters: Dict[str, Any], time_range: Dict[str, Any]) -> List[Dict[str, Any]]:
		categories = set((filters or {}).get("categories") or [])
		vendors = set((filters or {}).get("vendors") or [])
		min_amount = (filters or {}).get("min_amount")
		max_amount = (filters or {}).get("max_amount")
		tr = self._normalize_period(time_range or {})
		start_date_str = tr.get("start_date")
		end_date_str = tr.get("end_date")

		def parse_row_date(value: Any) -> Optional[date]:
			try:
				if not value:
					return None
				return datetime.strptime(str(value), "%Y-%m-%d").date()
			except Exception:
				return None

		start_dt = None
		end_dt = None
		try:
			start_dt = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
		except Exception:
			start_dt = None
		try:
			end_dt = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
		except Exception:
			end_dt = None

		def matches(row: Dict[str, Any]) -> bool:
			if categories and row.get("category") not in categories:
				return False
			if vendors and row.get("vendor") not in vendors:
				return False
			try:
				amt = float(row.get("amount", 0) or 0)
			except Exception:
				amt = 0
			if min_amount is not None and amt < float(min_amount):
				return False
			if max_amount is not None and amt > float(max_amount):
				return False
			if start_dt or end_dt:
				rd = parse_row_date(row.get("date"))
				if start_dt and (rd is None or rd < start_dt):
					return False
				if end_dt and (rd is None or rd > end_dt):
					return False
			return True

		return [r for r in rows if matches(r)]

	@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, min=0.2, max=2))
	def _extract_text_with_retry(self, path: str) -> str:
		return self.text_extractor.extract(path)

	@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, min=0.2, max=2))
	def _process_receipt_with_retry(self, text: str) -> Dict[str, Any]:
		return self.receipt_processor.process(text)

	@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, min=0.2, max=2))
	def _append_with_retry(self, expense: Dict[str, Any]) -> None:
		self.sheets.append_expense(expense)

	def _is_duplicate(self, expense: Dict[str, Any]) -> bool:
		if not self.settings.rules.duplicate_detection_enabled:
			return False
		rows = self.sheets.query_expenses({})
		for row in rows:
			try:
				if (
					str(row.get("vendor", "")).strip().lower() == str(expense.get("vendor", "")).strip().lower()
					and str(row.get("date", "")).strip() == str(expense.get("date", "")).strip()
					and float(row.get("amount", 0)) == float(expense.get("amount", 0))
				):
					return True
			except Exception:
				continue
		return False

	def handle_file_shared(self, body: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Process a file upload event.
		Expected body keys (for tests/local):
		- local_path: path to the uploaded file (tests use a local path; no network)
		- receipt_link: optional URL or reference to persist alongside the record
		"""
		local_path = body.get("local_path")
		if not local_path:
			return {"status": "error", "message": "local_path missing"}

		logger.debug("Starting OCR for: %s", local_path)
		text = self._extract_text_with_retry(local_path)

		logger.debug("Processing receipt text; length=%d", len(text))
		receipt = self._process_receipt_with_retry(text)

		# Ensure confidence exists if provided by model; keep as-is otherwise
		confidence = receipt.get("confidence")
		receipt_link = body.get("receipt_link", "")

		expense = {
			"date": receipt.get("date"),
			"vendor": receipt.get("vendor"),
			"amount": receipt.get("amount"),
			"category": receipt.get("category"),
			"description": receipt.get("description", ""),
			"receipt_link": receipt_link,
			"confidence": confidence,
			"payment_method": receipt.get("payment_method", ""),
			"receipt_number": receipt.get("receipt_number", ""),
			"tax_amount": receipt.get("tax_amount", ""),
			"location": receipt.get("location", ""),
		}

		if self._is_duplicate(expense):
			logger.info("Duplicate receipt detected: vendor=%s date=%s amount=%s", expense.get("vendor"), expense.get("date"), expense.get("amount"))
			return {"status": "duplicate", "expense": expense}

		self._append_with_retry(expense)
		logger.info("Receipt appended to sheet: vendor=%s date=%s amount=%s", expense.get("vendor"), expense.get("date"), expense.get("amount"))
		return {"status": "appended", "expense": expense} 