from __future__ import annotations

from typing import Any, Dict, Optional, List, Tuple
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
import re

from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import load_settings
from tools.text_extractor import TextExtractor
from tools.receipt_processor import ReceiptProcessor
from tools.sheets_manager import SheetsManager
from tools.query_analyzer import QueryAnalyzer
from tools.receipt_processor import _extract_total_from_text


logger = logging.getLogger(__name__)


def _fmt_money(value: float) -> str:
	try:
		amt = float(value or 0)
	except Exception:
		amt = 0.0
	return f"${amt:,.2f}"


class Controller:
	def __init__(self, text_extractor: TextExtractor, receipt_processor: ReceiptProcessor, sheets_manager: SheetsManager, query_analyzer: Optional[QueryAnalyzer] = None) -> None:
		self.text_extractor = text_extractor
		self.receipt_processor = receipt_processor
		self.sheets = sheets_manager
		self.settings = load_settings()
		self.query_analyzer = query_analyzer

	def _infer_vendor_from_query(self, query: str, rows: List[Dict[str, Any]]) -> Optional[str]:
		# Only infer when query explicitly mentions a vendor via preposition or is a short vendor-only query
		known_vendors = {str(r.get("vendor", "")).strip() for r in rows if r.get("vendor")}
		if not query or not known_vendors:
			return None
		# Explicit preposition pattern
		m = re.search(r"\b(?:on|at|from|in)\s+([A-Za-z][A-Za-z0-9 '&.-]{1,60})\b", query, flags=re.IGNORECASE)
		candidates: List[str] = []
		if m:
			candidates.append(m.group(1).strip())
		# If the whole query is very short (<= 3 tokens), try exact token matching
		tokens = [t for t in re.split(r"[^A-Za-z0-9&'.-]+", query) if t]
		stop = {"top", "categories", "category", "this", "last", "month", "week", "year", "by", "processed", "date", "how", "much", "have", "i", "spent", "total", "sum"}
		if len(tokens) <= 3 and any(t.lower() not in stop for t in tokens):
			candidates.extend(tokens)
		# Normalize and require token overlap, not substring
		def vendor_tokens(name: str) -> set[str]:
			return {t.lower() for t in re.split(r"[^A-Za-z0-9&'.-]+", name) if t}
		best: Optional[Tuple[int, str]] = None
		for cand in candidates:
			cand_tokens = vendor_tokens(cand)
			if not cand_tokens:
				continue
			for v in known_vendors:
				vt = vendor_tokens(v)
				overlap = cand_tokens & vt
				if overlap and len(overlap) == len(cand_tokens):
					score = len(vt)
					if best is None or score > best[0]:
						best = (score, v)
		return best[1] if best else None

	def handle_query(self, text: str) -> str:
		if not self.query_analyzer:
			return f"Received query: {text}"
		plan = self.query_analyzer.analyze(text)
		rows = self.sheets.query_expenses({})
		logger.info("Plan: intent=%s group_by=%s trend=%s top_n=%s filters=%s time_range=%s", plan.get("intent"), plan.get("group_by"), plan.get("trend"), plan.get("top_n"), plan.get("filters"), plan.get("time_range"))
		filters = dict(plan.get("filters") or {})
		# Only infer vendor when the plan is vendor-targeted (not category-focused)
		top_dim = ((plan.get("top_n") or {}).get("dimension"))
		group_by = plan.get("group_by")
		vendor_targeted = (top_dim == "vendor") or (group_by == "vendor") or (plan.get("intent") in {"summary", "search"} and top_dim != "category" and group_by != "category")
		if vendor_targeted and not (filters.get("vendors") or []):
			guess = self._infer_vendor_from_query(text, rows)
			if guess:
				filters["vendors"] = [guess]
				logger.info("Inferred vendor from query: %s", guess)
		time_range = plan.get("time_range") or {}
		filtered = self._apply_filters(rows, filters, time_range)
		logger.info("Filtered rows by date: %d", len(filtered))
		# Fallback: if no matches by receipt date, try processed_date range
		if not filtered and (time_range or {}).get("relative"):
			filtered = self._apply_filters(rows, filters, time_range, use_processed_date=True)
			logger.info("Filtered rows by processed_date: %d", len(filtered))
			# If still none and a category filter was applied, relax it
			if not filtered and (filters.get("categories") or []):
				relaxed = dict(filters)
				relaxed["categories"] = None
				filtered = self._apply_filters(rows, relaxed, time_range, use_processed_date=True)
				logger.info("Relaxed category filter; rows after relax: %d", len(filtered))
		intent = plan.get("intent", "summary")
		output_fmt = ((plan.get("output") or {}).get("format")) or "summary"
		vendor_filter = (filters.get("vendors") or []) if isinstance(filters.get("vendors"), list) else []

		if (plan.get("compare") or {}).get("enabled"):
			return self._execute_compare(rows, plan)

		if intent == "search":
			if output_fmt in {"table", "detailed"}:
				return self._render_table(filtered)
			return f"Found {len(filtered)} matching expenses"

		if intent == "top_n" or (plan.get("top_n") or {}).get("enabled"):
			# If a single vendor is specified, answer directly with their total
			if len(vendor_filter) == 1:
				total = sum(self._to_float(r.get("amount")) for r in filtered)
				count = len(filtered)
				return f"Your total spend on {vendor_filter[0]} is *{_fmt_money(total)}* ({count} transactions)"
			dim = (plan.get("top_n") or {}).get("dimension") or "vendor"
			limit = int((plan.get("top_n") or {}).get("limit") or 5)
			top = self._aggregate_top(filtered, dim, limit)
			parts = [f"{k}: {v:.2f}" for k, v in top]
			return f"Summary: Top {limit} {dim}(s): " + "; ".join(parts) if parts else "No data"

		group_by = plan.get("group_by", "none")
		trend = plan.get("trend") or {"enabled": False, "granularity": "month"}
		if intent == "trend" or trend.get("enabled"):
			gran = trend.get("granularity", "month")
			series = self._aggregate_trend(filtered, gran)
			if output_fmt == "chart":
				chart = (plan.get("output") or {}).get("chart") or {}
				return self._render_chart_series(series, chart)
			return self._render_grouped(series, key_label="date")

		if intent == "aggregate" or group_by in {"vendor", "category", "date"}:
			series = self._aggregate_group(filtered, group_by if group_by in {"vendor", "category", "date"} else "vendor")
			if output_fmt == "chart":
				chart = (plan.get("output") or {}).get("chart") or {}
				return self._render_chart_series(series, chart)
			return self._render_grouped(series, key_label=group_by)

		# Default summary
		total = sum(self._to_float(r.get("amount")) for r in filtered)
		count = len(filtered)
		if len(vendor_filter) == 1:
			return f"Your total spend on {vendor_filter[0]} is *{_fmt_money(total)}* ({count} transactions)"
		vendor_totals: Dict[str, float] = defaultdict(float)
		for r in filtered:
			vendor_totals[str(r.get("vendor", "Unknown"))] += self._to_float(r.get("amount"))
		limit = max(1, int(self.settings.rules.top_vendors_limit or 5))
		top_vendors = sorted(vendor_totals.items(), key=lambda kv: kv[1], reverse=True)[:limit]
		vendors_str = "; ".join(f"{v}: {amt:.2f}" for v, amt in top_vendors) if top_vendors else "None"
		return f"Summary: {count} expenses totaling {total:.2f}. Top vendors: {vendors_str}"

	def _render_grouped(self, series: List[Tuple[str, float, int]], key_label: str) -> str:
		# Simple textual listing
		if not series:
			return "No results"
		# Sort by total desc by default
		series = sorted(series, key=lambda x: x[1], reverse=True)
		parts = [f"{k}: {_fmt_money(total)} ({cnt} transactions)" for k, total, cnt in series]
		return "; ".join(parts)

	def _render_chart_series(self, series: List[Tuple[str, float, int]], chart: Dict[str, Any]) -> str:
		chart_type = (chart or {}).get("type") or "bar"
		dim = (chart or {}).get("dimension") or "date"
		metric = (chart or {}).get("metric") or "total"
		points = len(series)
		return f"Chart series prepared: type={chart_type}, dimension={dim}, metric={metric}, points={points}"

	def _render_table(self, rows: List[Dict[str, Any]]) -> str:
		headers = ["Date", "Vendor", "Amount", "Category"]
		lines = [" | ".join(headers)]
		for r in rows:
			lines.append(" | ".join([
				str(r.get("date", "")),
				str(r.get("vendor", "")),
				f"{self._to_float(r.get('amount')):.2f}",
				str(r.get("category", "")),
			]))
		# Log a small preview for debugging
		logger.info("Rendered table with %d rows", max(0, len(rows) - 1))
		return "\n".join(lines)

	def _to_float(self, v: Any) -> float:
		try:
			return float(v or 0)
		except Exception:
			return 0.0

	def _parse_row_date(self, value: Any) -> Optional[date]:
			try:
				if not value:
					return None
				return datetime.strptime(str(value), "%Y-%m-%d").date()
			except Exception:
				return None

	def _parse_processed_date(self, value: Any) -> Optional[date]:
		try:
			if not value:
				return None
			# processed_date is ISO string
			return datetime.fromisoformat(str(value)).date()
		except Exception:
			return None

	def _normalize_time_range(self, time_range: Dict[str, Any]) -> Tuple[Optional[date], Optional[date]]:
		tr = time_range or {}
		start_str = tr.get("start_date")
		end_str = tr.get("end_date")
		rel = tr.get("relative")
		start_dt = None
		end_dt = None
		# Resolve relative if provided (takes precedence to ensure consistency with current runtime date)
		if rel:
			today = date.today()
			if rel == "this_month":
				start_dt = today.replace(day=1)
				end_dt = today
			elif rel == "last_month":
				first_this = today.replace(day=1)
				last_prev = first_this - timedelta(days=1)
				start_dt = last_prev.replace(day=1)
				end_dt = last_prev
			elif rel == "this_year":
				start_dt = today.replace(month=1, day=1)
				end_dt = today
			elif rel == "last_7_days":
				start_dt = today - timedelta(days=7)
				end_dt = today
			elif rel == "last_90_days":
				start_dt = today - timedelta(days=90)
				end_dt = today
			elif rel == "last_quarter":
				q = (today.month - 1) // 3 + 1
				lq = q - 1 if q > 1 else 4
				year = today.year if q > 1 else today.year - 1
				start_month = 3 * (lq - 1) + 1
				start_dt = date(year, start_month, 1)
				end_month = start_month + 2
				next_first = date(year + (1 if end_month == 12 and 12 == 12 else 0), (end_month % 12) + 1, 1)
				end_dt = next_first - timedelta(days=1)
		# explicit dates override if no relative provided
		if not rel:
			try:
				if start_str:
					start_dt = datetime.strptime(start_str, "%Y-%m-%d").date()
			except Exception:
				pass
			try:
				if end_str:
					end_dt = datetime.strptime(end_str, "%Y-%m-%d").date()
			except Exception:
				pass
		return start_dt, end_dt

	def _apply_filters(self, rows: List[Dict[str, Any]], filters: Dict[str, Any], time_range: Dict[str, Any], use_processed_date: bool = False) -> List[Dict[str, Any]]:
		categories = set((filters or {}).get("categories") or [])
		vendors = set((filters or {}).get("vendors") or [])
		min_amount = (filters or {}).get("min_amount")
		max_amount = (filters or {}).get("max_amount")
		text_search = (filters or {}).get("text_search")
		start_dt, end_dt = self._normalize_time_range(time_range or {})

		needle = str(text_search or "").strip().lower()

		def matches(row: Dict[str, Any]) -> bool:
			if categories and row.get("category") not in categories:
				return False
			if vendors and row.get("vendor") not in vendors:
				return False
			amt = self._to_float(row.get("amount"))
			if min_amount is not None and amt < float(min_amount):
				return False
			if max_amount is not None and amt > float(max_amount):
				return False
			if start_dt or end_dt:
				if use_processed_date:
					rd = self._parse_processed_date(row.get("Processed_Date") or row.get("processed_date"))
				else:
					rd = self._parse_row_date(row.get("date"))
				if start_dt and (rd is None or rd < start_dt):
					return False
				if end_dt and (rd is None or rd > end_dt):
					return False
			if needle:
				blob = " ".join([
					str(row.get("description", "")),
					str(row.get("vendor", "")),
					str(row.get("location", "")),
				]).lower()
				if needle not in blob:
					return False
			return True

		return [r for r in rows if matches(r)]

	def _aggregate_group(self, rows: List[Dict[str, Any]], dim: str) -> List[Tuple[str, float, int]]:
		totals: Dict[str, float] = defaultdict(float)
		counts: Dict[str, int] = defaultdict(int)
		key = dim if dim in {"vendor", "category"} else "date"
		for r in rows:
			k = str(r.get(key, ""))
			val = self._to_float(r.get("amount"))
			totals[k] += val
			counts[k] += 1
		return [(k, totals[k], counts[k]) for k in totals.keys()]

	def _bucket_date(self, d: date, gran: str) -> str:
		if gran == "day":
			return d.isoformat()
		if gran == "week":
			year, week, _ = d.isocalendar()
			return f"{year}-W{int(week):02d}"
		if gran == "month":
			return f"{d.year}-{d.month:02d}"
		if gran == "quarter":
			q = (d.month - 1) // 3 + 1
			return f"{d.year}-Q{q}"
		if gran == "year":
			return f"{d.year}"
		return d.isoformat()

	def _aggregate_trend(self, rows: List[Dict[str, Any]], granularity: str) -> List[Tuple[str, float, int]]:
		totals: Dict[str, float] = defaultdict(float)
		counts: Dict[str, int] = defaultdict(int)
		gran = granularity or "month"
		for r in rows:
			rd = self._parse_row_date(r.get("date"))
			if not rd:
				continue
			key = self._bucket_date(rd, gran)
			totals[key] += self._to_float(r.get("amount"))
			counts[key] += 1
		# Sort keys by date ordering where possible
		def sort_key(item: Tuple[str, float, int]) -> Tuple[int, str]:
			k = item[0]
			# Try to parse common formats
			try:
				if gran in {"day"}:
					return (0, k)
				if gran == "month":
					return (0, k)
				if gran == "year":
					return (0, k)
				if gran == "week":
					return (0, k)
				if gran == "quarter":
					return (0, k)
			except Exception:
				pass
			return (1, k)
		series = [(k, totals[k], counts[k]) for k in totals.keys()]
		return sorted(series, key=sort_key)

	def _aggregate_top(self, rows: List[Dict[str, Any]], dimension: str, limit: int) -> List[Tuple[str, float]]:
		dim = dimension if dimension in {"vendor", "category"} else "vendor"
		totals: Dict[str, float] = defaultdict(float)
		for r in rows:
			k = str(r.get(dim, ""))
			totals[k] += self._to_float(r.get("amount"))
		items = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
		return items[: max(1, int(limit))]

	def _execute_compare(self, all_rows: List[Dict[str, Any]], plan: Dict[str, Any]) -> str:
		filters = plan.get("filters", {})
		cmp = plan.get("compare") or {}
		baseline = cmp.get("baseline") or {}
		target = cmp.get("target") or {}
		def _sum_for_range(rng: Dict[str, Any]) -> Tuple[float, int]:
			rows = self._apply_filters(all_rows, filters, {"start_date": rng.get("start_date"), "end_date": rng.get("end_date"), "relative": None})
			# Try processed_date if no match
			if not rows:
				rows = self._apply_filters(all_rows, filters, {"start_date": rng.get("start_date"), "end_date": rng.get("end_date"), "relative": None}, use_processed_date=True)
			total = sum(self._to_float(r.get("amount")) for r in rows)
			return total, len(rows)
		b_total, b_count = _sum_for_range(baseline)
		t_total, t_count = _sum_for_range(target)
		delta = t_total - b_total
		pct = (delta / b_total * 100.0) if b_total else 0.0
		return f"Compare: baseline total {b_total:.2f} ({b_count}); target total {t_total:.2f} ({t_count}); delta {delta:.2f} ({pct:.1f}%)"

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

	def _infer_vendor_from_text(self, text: str) -> str | None:
		lines = [ln.strip() for ln in (text or '').splitlines() if ln.strip()]
		candidates = []
		skip_words = {"subtotal", "total", "tax", "cash", "change", "open", "manager", "items", "sold", "discount", "receipt"}
		for ln in lines[:10]:
			up = ln.upper()
			if any(marker in up for marker in {"[IMAGE_BASE64_BEGIN", "DATA:IMAGE", "BASE64"}):
				continue
			if any(w in up for w in {"SUBTOTAL", "TOTAL", "CASH", "CHANGE", "DATE", "TIME"}):
				continue
			alpha_ratio = sum(ch.isalpha() for ch in ln) / max(1, len(ln))
			if alpha_ratio < 0.4:
				continue
			words = [w for w in re.split(r"[^A-Za-z]+", ln) if w]
			if any(w.lower() in skip_words for w in words):
				continue
			candidates.append(ln)
		if not candidates:
			return None
		raw = candidates[0]
		name = raw.replace("*", "").strip()
		if name.upper().startswith("WALMART") or name.upper().startswith("WALMART") or name.upper().startswith("WALMART"):
			name = "Walmart"
		if name.upper().startswith("WALMART") or "WALMART" in name.upper() or "WAL-MART" in name.upper():
			name = "Walmart"
		return name

	def _infer_location_from_text(self, text: str) -> str | None:
		lines = [ln.strip() for ln in (text or '').splitlines() if ln.strip()]
		addr_candidates: list[str] = []
		# Very naive: look for a line that contains digits and a street-type keyword, or a city/state format
		for ln in lines[:20]:
			if len(addr_candidates) >= 2:
				break
			upper = ln.upper()
			if any(k in upper for k in {" ST", " AVE", " ROAD", " RD", " DRIVE", " DR", " BLVD", " PARK", " WAY"}) and any(ch.isdigit() for ch in ln):
				addr_candidates.append(ln)
				continue
			# city, state pattern: Dallas TX or San Francisco, CA
			if re.search(r"[A-Za-z]+\s+[A-Z]{2}\s*\d{4,5}", ln):
				addr_candidates.append(ln)
		if addr_candidates:
			return ", ".join(addr_candidates)
		return None

	def _infer_description_from_text(self, text: str) -> str | None:
		# Use first two item lines that look like product lines (letters + amount) before totals
		lines = [ln.strip() for ln in (text or '').splitlines() if ln.strip()]
		item_lines: list[str] = []
		amount_re = re.compile(r"\d+[\.,]\d{2}")
		for ln in lines:
			if len(item_lines) >= 2:
				break
			upper = ln.upper()
			if any(k in upper for k in {"SUBTOTAL", "TOTAL", "AMOUNT"}):
				break
			if amount_re.search(ln) and any(ch.isalpha() for ch in ln):
				item_lines.append(ln.split(amount_re.search(ln).group(0))[0].strip())
		if item_lines:
			return "; ".join(item_lines)
		return None

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
		if not text or len(text.strip()) < 20:
			logger.error("Transcription returned insufficient text; length=%d", len(text.strip()) if text else 0)
			return {"status": "error", "message": "insufficient_text"}

		# Bail out if transcript is clearly not natural text (e.g., base64 echo or placeholders)
		upper_preview = (text[:256] or "").upper()
		if "[IMAGE_BASE64_BEGIN" in upper_preview or upper_preview.startswith("DATA:IMAGE"):
			logger.error("Transcript appears to be non-text content (base64/placeholder). Aborting processing.")
			return {"status": "error", "message": "invalid_transcript"}

		# Sanitize markdown-style headings injected by vision model (e.g., '**Header**')
		def _sanitize_md_headings(raw: str) -> str:
			lines = []
			for ln in raw.splitlines():
				trim = ln.strip()
				if trim.startswith("**") and trim.endswith("**") and len(trim) < 80:
					# drop markdown heading lines
					continue
				# strip bold markers inside line
				ln = ln.replace("**", "")
				lines.append(ln)
			return "\n".join(lines)
		text = _sanitize_md_headings(text)

		# Log a redacted preview of the transcript used for structuring (first 10 lines)
		try:
			def _redact(sample: str) -> str:
				masked = sample
				# Mask long digit runs that look like card numbers or phone numbers
				masked = __import__("re").sub(r"(?<!\d)\d{12,16}(?!\d)", "************", masked)
				# Mask emails
				masked = __import__("re").sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "***@***", masked)
				return masked
			preview_lines = [ln for ln in (text or "").splitlines() if ln][:10]
			logger.info("Transcript preview (first 10 lines):\n%s", _redact("\n".join(preview_lines)))
		except Exception:
			pass

		logger.debug("Processing receipt text; length=%d", len(text))
		try:
			receipt = self._process_receipt_with_retry(text)
		except Exception as e:
			logger.error("LLM extraction failed after retries; falling back to basic heuristics: %s", e)
			# Basic heuristic fallback
			receipt = {
				"vendor": self._infer_vendor_from_text(text) or "Unknown",
				"amount": _extract_total_from_text(text) or 0,
				"date": (re.search(r"(\d{4}[/-]\d{2}[/-]\d{2})", text) or re.search(r"(\d{2}[/-]\d{2}[/-]\d{2,4})", text) or [None])[0] if re.search(r"\d", text) else None,
				"category": "Other Business Expenses",
				"description": self._infer_description_from_text(text) or "Unclassified items",
				"location": self._infer_location_from_text(text) or "",
				"receipt_number": None,
			}
			if not receipt["date"]:
				receipt["date"] = datetime.today().strftime("%Y-%m-%d")

		# Ensure confidence exists if provided by model; keep as-is otherwise
		confidence = receipt.get("confidence")
		receipt_link = body.get("receipt_link", "")

		# Override amount with reliable OCR total if found and seems plausible
		try:
			parsed_total = _extract_total_from_text(text)
			if parsed_total is not None:
				# Prefer the larger between model and parsed total to avoid partial sums
				model_amt = receipt.get("amount")
				model_amt_f = float(model_amt) if model_amt is not None else 0.0
				if parsed_total > 0 and (model_amt is None or parsed_total >= model_amt_f * 0.95):
					receipt["amount"] = parsed_total
			# Vendor inference from text header
			inferred_vendor = self._infer_vendor_from_text(text)
			if inferred_vendor:
				model_vendor = str(receipt.get("vendor") or "").strip()
				if model_vendor and model_vendor.lower() not in (text or "").lower():
					receipt["vendor"] = inferred_vendor
			# Location inference
			if not receipt.get("location"):
				loc = self._infer_location_from_text(text)
				if loc:
					receipt["location"] = loc
			# Description inference
			if not receipt.get("description"):
				desc = self._infer_description_from_text(text)
				if desc:
					receipt["description"] = desc
		except Exception:
			pass

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