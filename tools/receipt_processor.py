from typing import Any, Dict
from pathlib import Path
import json
import logging
import re

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from config.prompts import RECEIPT_EXTRACTION_PROMPT


logger = logging.getLogger(__name__)


def _strip_code_fences(text: str) -> str:
	"""
	Remove Markdown code fences like ```json ... ``` or ``` ... ``` if present.
	Returns the inner content if fences are found; otherwise returns original text.
	"""
	if "```" not in text:
		return text
	# Prefer fenced json blocks
	m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
	if m:
		return m.group(1).strip()
	return text


def _extract_balanced_json_object(text: str) -> Dict[str, Any]:
	"""
	Extract the first balanced JSON object from text, ignoring braces within quoted strings.
	Raises json.JSONDecodeError if none found or if parsing fails.
	"""
	clean = _strip_code_fences(text)
	in_string: str | None = None
	escape = False
	start_idx = -1
	depth = 0
	for idx, ch in enumerate(clean):
		if escape:
			escape = False
			continue
		if ch == "\\":
			escape = True
			continue
		if ch in {'"', "'"}:
			if in_string is None:
				in_string = ch
			elif in_string == ch:
				in_string = None
			continue
		if in_string is not None:
			continue
		if ch == "{":
			if depth == 0:
				start_idx = idx
			depth += 1
		elif ch == "}":
			if depth > 0:
				depth -= 1
				if depth == 0 and start_idx != -1:
					candidate = clean[start_idx:idx + 1]
					try:
						return json.loads(candidate)
					except Exception:
						# As a last resort, remove raw control chars and retry once
						sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", candidate)
						return json.loads(sanitized)
	raise json.JSONDecodeError("No balanced JSON object found", clean, 0)


def _try_extract_json_object(text: str) -> Dict[str, Any]:
	start = text.find("{")
	if start == -1:
		raise json.JSONDecodeError("No JSON object braces found", text, 0)
	# Progressively attempt to parse up to each closing brace
	for idx in range(start + 1, len(text)):
		if text[idx] == "}":
			candidate = text[start:idx + 1]
			try:
				return json.loads(candidate)
			except Exception:
				continue
	# Fall back to balanced parser that ignores braces in strings and strips fences
	return _extract_balanced_json_object(text)


def _extract_total_from_text(text: str) -> float | None:
	"""
	Find a reliable TOTAL amount from OCR text using simple heuristics:
	- Prefer a line containing the standalone word TOTAL (not SUBTOTAL)
	- Use the rightmost amount-like token on that line (e.g., 38.68)
	- Fallback to AMOUNT DUE / BALANCE DUE if present
	Returns a float or None if no confident amount is found.
	"""
	lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
	amount_pattern = re.compile(r"(?<![\d])([\$€£₦]?\s?\d{1,4}(?:[.,]\d{2}))\b")
	candidates: list[float] = []
	for ln in lines:
		upper = ln.upper()
		if "SUBTOTAL" in upper:
			continue
		if re.search(r"\b(TOTAL|AMOUNT DUE|BALANCE DUE)\b", upper):
			amts = amount_pattern.findall(ln)
			if amts:
				# choose the rightmost amount on the line
				raw = amts[-1]
				num = raw.replace(" ", "").lstrip("$€£₦").replace(",", ".")
				try:
					candidates.append(round(float(num), 2))
				except Exception:
					continue
	# Return the first found candidate
	return candidates[0] if candidates else None


class ReceiptProcessor:
	def __init__(self, granite_client: Any) -> None:
		self.granite = granite_client
		# Load receipt schema once
		schema_path = Path(__file__).resolve().parents[1] / "data" / "schemas" / "receipt_schema.json"
		with open(schema_path, "r", encoding="utf-8") as f:
			self._schema = json.load(f)

	def _normalize_fields(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
		# Normalize items: allow list of strings by converting to list of {name}
		items = parsed.get("items")
		if isinstance(items, list):
			normalized = []
			for it in items:
				if isinstance(it, str):
					normalized.append({"name": it})
				elif isinstance(it, dict):
					normalized.append(it)
				else:
					continue
			parsed["items"] = normalized
		return parsed

	def process(self, receipt_text: str) -> Dict[str, Any]:
		# Trim very long receipts to improve JSON success: keep first 40 and last 40 lines
		lines = receipt_text.splitlines()
		if len(lines) > 120:
			trimmed_lines = lines[:40] + ["..."] + lines[-40:]
			receipt_trimmed = "\n".join(trimmed_lines)
		else:
			receipt_trimmed = receipt_text
		prompt = RECEIPT_EXTRACTION_PROMPT.format(receipt_text=receipt_trimmed)
		logger.info("ReceiptProcessor.process: sending text_length=%d", len(receipt_text))
		response_text = self.granite.generate(prompt)

		# Parse JSON returned by model
		try:
			parsed = self.granite.parse_json(response_text)
		except json.JSONDecodeError:
			# Conservative fallback: extract first valid JSON object if present
			try:
				parsed = _try_extract_json_object(response_text)
			except Exception as e:
				logger.warning("Granite returned invalid JSON; attempting one retry with strict JSON-only instruction")
				strict_prompt = (
					"ONLY return a valid minified JSON object that matches the schema above. "
					"Do not use markdown, explanations, or extra keys. If unsure set value to null.\n\n" + prompt
				)
				try:
					response_text2 = self.granite.generate(strict_prompt)
					parsed = self.granite.parse_json(response_text2)
				except Exception:
					logger.error("Granite retry still returned invalid JSON")
					raise ValueError("Model returned invalid JSON") from e

		logger.info("ReceiptProcessor.process: parsed JSON successfully")
		# Normalize fields for schema compatibility
		parsed = self._normalize_fields(parsed)

		# Validate against schema
		try:
			validate(instance=parsed, schema=self._schema)
		except ValidationError as e:
			logger.warning("Receipt JSON failed schema validation: %s", e.message)
			raise

		return parsed 