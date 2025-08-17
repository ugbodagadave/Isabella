import json
import logging
import time
from typing import Any, Dict, Optional

import requests

from config.settings import load_settings


logger = logging.getLogger(__name__)


class GraniteClient:
	def __init__(self) -> None:
		self.settings = load_settings()
		self._iam_token: Optional[str] = None
		self._iam_token_exp: float = 0.0
		self._iam_url = "https://iam.cloud.ibm.com/identity/token"
		self._generation_version = "2023-05-29"

	def build_request(self, prompt: str, temperature: float = 0.1, max_tokens: int = 512) -> Dict[str, Any]:
		payload = {
			"model_id": self.settings.watsonx.model_id,
			"project_id": self.settings.watsonx.project_id,
			"input": prompt,
			"parameters": {
				"decoding_method": "greedy",
				"temperature": temperature,
				"max_new_tokens": max_tokens,
				"repetition_penalty": 1.0,
				"json_output": True,
				"format": "json",
			},
		}
		logger.debug("Built Granite request payload: model_id=%s len(prompt)=%d", self.settings.watsonx.model_id, len(prompt))
		return payload

	def _ensure_token(self) -> str:
		now = time.time()
		if self._iam_token and now < self._iam_token_exp - 60:
			return self._iam_token
		resp = requests.post(
			self._iam_url,
			headers={"Content-Type": "application/x-www-form-urlencoded"},
			data={
				"grant_type": "urn:ibm:params:oauth:grant-type:apikey",
				"apikey": self.settings.watsonx.api_key,
			},
			timeout=30,
		)
		resp.raise_for_status()
		data = resp.json()
		self._iam_token = data.get("access_token")
		expires_in = float(data.get("expires_in", 3600))
		self._iam_token_exp = now + expires_in
		return self._iam_token  # type: ignore[return-value]

	def generate(self, prompt: str, temperature: float = 0.1, max_tokens: int = 512) -> str:
		"""Invoke IBM Watsonx text generation for Granite models.

		This is used by live E2E tests. Unit tests should continue mocking this method.
		"""
		token = self._ensure_token()
		url = f"{self.settings.watsonx.url.rstrip('/')}/ml/v1/text/generation?version={self._generation_version}"
		payload = self.build_request(prompt, temperature=temperature, max_tokens=max_tokens)
		headers = {
			"Authorization": f"Bearer {token}",
			"Content-Type": "application/json",
			"Accept": "application/json",
		}
		resp = requests.post(url, headers=headers, json=payload, timeout=60)
		resp.raise_for_status()
		data = resp.json()
		# Expected shape: {"results": [{"generated_text": "..."}, ...]}
		results = data.get("results") or []
		if isinstance(results, list) and results:
			text = results[0].get("generated_json") or results[0].get("generated_text") or results[0].get("output_text")
			if text:
				return text
		# Fallback: try top-level text
		return data.get("generated_text") or json.dumps(data)

	def parse_json(self, text: str) -> Any:
		# Trim common Markdown fences and hints
		clean = text.strip()
		if clean.startswith("```") and clean.endswith("```"):
			clean = clean.strip("`")
			# Remove possible leading language tag like json\n
			first_newline = clean.find("\n")
			if first_newline != -1:
				clean = clean[first_newline + 1 :].strip()
		# Remove raw control characters that break json.loads
		clean = "".join(ch for ch in clean if ch >= " " or ch in "\t\n\r")
		return json.loads(clean) 