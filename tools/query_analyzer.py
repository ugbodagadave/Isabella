from __future__ import annotations

from typing import Any, Dict, Optional
import json
from datetime import date
import logging

from config.prompts import QUERY_ANALYSIS_PROMPT


logger = logging.getLogger(__name__)


class QueryAnalyzer:
	def __init__(self, granite_client: Any) -> None:
		self.granite = granite_client

	def analyze(self, user_query: str, current_date: Optional[str] = None) -> Dict[str, Any]:
		prompt = QUERY_ANALYSIS_PROMPT.format(
			user_query=user_query,
			current_date=current_date or date.today().isoformat(),
		)
		logger.debug("Analyzing query via Granite; len(query)=%d", len(user_query))
		text = self.granite.generate(prompt)
		try:
			return self.granite.parse_json(text)
		except json.JSONDecodeError as e:
			logger.error("Granite query analysis returned invalid JSON: %s", str(e))
			raise ValueError("Invalid JSON from query analysis") from e 