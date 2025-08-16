from __future__ import annotations

from typing import Any, Dict, Optional, List, Tuple
import json
from datetime import date, datetime, timedelta
import logging
import re

from config.prompts import QUERY_ANALYSIS_PROMPT


logger = logging.getLogger(__name__)

_ALLOWED_INTENTS = {"summary", "search", "aggregate", "trend", "top_n", "compare"}
_ALLOWED_GROUP_BY = {"none", "vendor", "category", "date"}
_ALLOWED_TREND_GRAN = {"day", "week", "month", "quarter", "year"}
_ALLOWED_TOP_DIM = {"vendor", "category"}
_ALLOWED_SORT_BY = {"amount", "date", "vendor", "category", "count", "total"}
_ALLOWED_SORT_DIR = {"asc", "desc"}
_ALLOWED_OUTPUT_FMT = {"summary", "table", "detailed", "chart"}
_ALLOWED_CHART_TYPE = {"bar", "line", "pie", "area", None}
_ALLOWED_CHART_DIM = {"vendor", "category", "date", None}
_ALLOWED_CHART_METRIC = {"amount", "count", "total", None}


class QueryAnalyzer:
	def __init__(self, granite_client: Any) -> None:
		self.granite = granite_client

	def _default_plan(self) -> Dict[str, Any]:
		return {
			"intent": "summary",
			"time_range": {"start_date": None, "end_date": None, "relative": None},
			"filters": {"vendors": None, "categories": None, "min_amount": None, "max_amount": None, "text_search": None},
			"group_by": "none",
			"trend": {"enabled": False, "granularity": "month"},
			"top_n": {"enabled": False, "dimension": "vendor", "limit": 5},
			"compare": {"enabled": False, "baseline": None, "target": None},
			"sort": {"by": "date", "direction": "desc"},
			"output": {"format": "summary", "chart": {"type": None, "dimension": None, "metric": None}},
		}

	def _strip_code_fences(self, text: str) -> str:
		clean = text.strip()
		if clean.startswith("```") and clean.endswith("```"):
			clean = clean.strip("`")
			first_newline = clean.find("\n")
			if first_newline != -1:
				clean = clean[first_newline + 1 :].strip()
		return clean

	def _extract_first_json(self, text: str) -> Optional[str]:
		# Extract first balanced {...} block
		start = None
		brace = 0
		for i, ch in enumerate(text):
			if ch == '{':
				if brace == 0:
					start = i
				brace += 1
			elif ch == '}':
				if brace > 0:
					brace -= 1
					if brace == 0 and start is not None:
						return text[start : i + 1]
		return None

	def _parse_json(self, text: str) -> Any:
		try:
			if hasattr(self.granite, "parse_json"):
				return self.granite.parse_json(text)
			clean = self._strip_code_fences(text)
			clean = "".join(ch for ch in clean if ch >= " " or ch in "\t\n\r")
			return json.loads(clean)
		except json.JSONDecodeError:
			# Try extracting first JSON object from mixed output
			clean2 = self._strip_code_fences(text)
			snippet = self._extract_first_json(clean2)
			if snippet:
				try:
					return json.loads(snippet)
				except Exception:
					pass
			logger.error("Granite query analysis returned invalid JSON: could not extract a valid JSON object")
			raise ValueError("Invalid JSON from query analysis")

	def _coerce_list_str(self, value: Any) -> Optional[List[str]]:
		if value is None:
			return None
		if isinstance(value, list):
			return [str(v) for v in value if v is not None]
		if isinstance(value, str) and value.strip():
			return [value.strip()]
		return None

	def _coerce_float(self, value: Any) -> Optional[float]:
		if value is None or value == "":
			return None
		try:
			return float(value)
		except Exception:
			return None

	def _ensure_enum(self, value: Any, allowed: set, default: Any) -> Any:
		return value if value in allowed else default

	def _resolve_relative_range(self, relative: Optional[str], today: date) -> Tuple[Optional[str], Optional[str]]:
		if not relative:
			return None, None
		rel = str(relative).lower()
		if rel == "this_month":
			start = today.replace(day=1)
			end = today
			return start.isoformat(), end.isoformat()
		if rel == "last_month":
			first_this = today.replace(day=1)
			last_prev = first_this - timedelta(days=1)
			start = last_prev.replace(day=1)
			return start.isoformat(), last_prev.isoformat()
		if rel == "this_year":
			start = today.replace(month=1, day=1)
			return start.isoformat(), today.isoformat()
		if rel == "last_7_days":
			start = today - timedelta(days=7)
			return start.isoformat(), today.isoformat()
		if rel == "last_90_days":
			start = today - timedelta(days=90)
			return start.isoformat(), today.isoformat()
		if rel == "last_quarter":
			q = (today.month - 1) // 3 + 1
			# last quarter
			last_q = q - 1 if q > 1 else 4
			year = today.year if q > 1 else today.year - 1
			start_month = 3 * (last_q - 1) + 1
			start = date(year, start_month, 1)
			# end of quarter
			end_month = start_month + 2
			# compute last day of end_month
			next_month_first = date(year + (1 if end_month == 12 and 12 == 12 else 0), (end_month % 12) + 1, 1)
			end = next_month_first - timedelta(days=1)
			return start.isoformat(), end.isoformat()
		# Custom or unsupported
		return None, None

	def _maybe_fill_dates(self, plan: Dict[str, Any], today: date) -> None:
		tr = plan.get("time_range") or {}
		rel = tr.get("relative")
		start = tr.get("start_date")
		end = tr.get("end_date")
		if (start is None or end is None) and rel:
			calc_start, calc_end = self._resolve_relative_range(rel, today)
			if start is None:
				tr["start_date"] = calc_start
			if end is None:
				tr["end_date"] = calc_end
		plan["time_range"] = tr

	def _normalize(self, raw: Dict[str, Any], today: date) -> Dict[str, Any]:
		plan = self._default_plan()
		# intent
		intent = (raw or {}).get("intent") or (raw or {}).get("query_type")
		plan["intent"] = self._ensure_enum(intent, _ALLOWED_INTENTS, "summary")
		# time_range
		raw_tr = (raw or {}).get("time_range") or {}
		tr = {
			"start_date": raw_tr.get("start_date"),
			"end_date": raw_tr.get("end_date"),
			"relative": raw_tr.get("relative") or raw_tr.get("period") or None,
		}
		plan["time_range"] = tr
		# filters
		raw_filters = (raw or {}).get("filters") or {}
		plan["filters"] = {
			"vendors": self._coerce_list_str(raw_filters.get("vendors")),
			"categories": self._coerce_list_str(raw_filters.get("categories")),
			"min_amount": self._coerce_float(raw_filters.get("min_amount")),
			"max_amount": self._coerce_float(raw_filters.get("max_amount")),
			"text_search": (str(raw_filters.get("text_search")).strip() if raw_filters.get("text_search") not in (None, "") else None),
		}
		# group_by
		plan["group_by"] = self._ensure_enum((raw or {}).get("group_by"), _ALLOWED_GROUP_BY, "none")
		# trend
		raw_trend = (raw or {}).get("trend") or {}
		plan["trend"] = {
			"enabled": bool(raw_trend.get("enabled", False)),
			"granularity": self._ensure_enum(raw_trend.get("granularity", "month"), _ALLOWED_TREND_GRAN, "month"),
		}
		# top_n
		raw_top = (raw or {}).get("top_n") or {}
		limit_val = raw_top.get("limit")
		try:
			limit_int = int(limit_val) if limit_val is not None else 5
		except Exception:
			limit_int = 5
		plan["top_n"] = {
			"enabled": bool(raw_top.get("enabled", False)),
			"dimension": self._ensure_enum(raw_top.get("dimension", plan["group_by"] if plan["group_by"] in _ALLOWED_TOP_DIM else "vendor"), _ALLOWED_TOP_DIM, "vendor"),
			"limit": max(1, limit_int),
		}
		# compare
		raw_cmp = (raw or {}).get("compare") or {}
		plan["compare"] = {
			"enabled": bool(raw_cmp.get("enabled", False)),
			"baseline": raw_cmp.get("baseline") if isinstance(raw_cmp.get("baseline"), dict) else None,
			"target": raw_cmp.get("target") if isinstance(raw_cmp.get("target"), dict) else None,
		}
		# sort
		raw_sort = (raw or {}).get("sort") or {}
		plan["sort"] = {
			"by": self._ensure_enum(raw_sort.get("by", "total" if plan["group_by"] != "none" or plan["trend"]["enabled"] else "date"), _ALLOWED_SORT_BY, "date"),
			"direction": self._ensure_enum(raw_sort.get("direction", "desc"), _ALLOWED_SORT_DIR, "desc"),
		}
		# output
		raw_out = (raw or {}).get("output") or {}
		raw_chart = raw_out.get("chart") or {}
		fmt = raw_out.get("format", "summary")
		fmt = self._ensure_enum(fmt, _ALLOWED_OUTPUT_FMT, "summary")
		chart = {
			"type": raw_chart.get("type"),
			"dimension": raw_chart.get("dimension"),
			"metric": raw_chart.get("metric"),
		}
		# sanitize chart enums allowing None
		chart_type = chart.get("type")
		chart_dim = chart.get("dimension")
		chart_metric = chart.get("metric")
		if chart_type not in _ALLOWED_CHART_TYPE:
			chart_type = None
		if chart_dim not in _ALLOWED_CHART_DIM:
			chart_dim = None
		if chart_metric not in _ALLOWED_CHART_METRIC:
			chart_metric = None
		plan["output"] = {"format": fmt, "chart": {"type": chart_type, "dimension": chart_dim, "metric": chart_metric}}

		# Fill dates from relative
		self._maybe_fill_dates(plan, today)
		return plan

	def analyze(self, user_query: str, current_date: Optional[str] = None) -> Dict[str, Any]:
		prompt = QUERY_ANALYSIS_PROMPT.format(
			user_query=user_query,
			current_date=current_date or date.today().isoformat(),
		)
		logger.debug("Analyzing query via Granite; len(query)=%d", len(user_query))
		text = self.granite.generate(prompt)
		raw = self._parse_json(text)
		# Normalize and validate
		today = date.fromisoformat(current_date) if current_date else date.today()
		plan = self._normalize(raw if isinstance(raw, dict) else {}, today)
		return plan 