from typing import Any, Dict
from pathlib import Path
import json
import logging

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from config.prompts import RECEIPT_EXTRACTION_PROMPT


logger = logging.getLogger(__name__)


class ReceiptProcessor:
	def __init__(self, granite_client: Any) -> None:
		self.granite = granite_client
		# Load receipt schema once
		schema_path = Path(__file__).resolve().parents[1] / "data" / "schemas" / "receipt_schema.json"
		with open(schema_path, "r", encoding="utf-8") as f:
			self._schema = json.load(f)

	def process(self, receipt_text: str) -> Dict[str, Any]:
		prompt = RECEIPT_EXTRACTION_PROMPT.format(receipt_text=receipt_text)
		logger.debug("Sending receipt text to Granite for extraction; text_length=%d", len(receipt_text))
		response_text = self.granite.generate(prompt)

		# Parse JSON returned by model
		try:
			parsed = self.granite.parse_json(response_text)
		except json.JSONDecodeError as e:
			logger.error("Granite returned invalid JSON: %s", str(e))
			raise ValueError("Model returned invalid JSON") from e

		# Validate against schema
		try:
			validate(instance=parsed, schema=self._schema)
		except ValidationError as e:
			logger.warning("Receipt JSON failed schema validation: %s", e.message)
			raise

		return parsed 