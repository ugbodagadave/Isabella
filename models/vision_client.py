import base64
import logging
import time
from typing import Any, Dict, List, Optional

import requests

from config.settings import load_settings


logger = logging.getLogger(__name__)


class VisionClient:
	"""
	Thin client for IBM watsonx multimodal (vision-instruct) models.
	Currently implements IAM token handling and a placeholder transcribe call.
	If the backend rejects the request, callers should fallback to classic OCR.
	"""

	def __init__(self, model_id: str, temperature: float = 0.0, max_tokens: int = 2048) -> None:
		self.settings = load_settings()
		self._iam_token: Optional[str] = None
		self._iam_token_exp: float = 0.0
		self._iam_url = "https://iam.cloud.ibm.com/identity/token"
		self.model_id = model_id
		self.temperature = float(temperature)
		self.max_tokens = int(max_tokens)

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

	def transcribe(self, images: List[bytes], instruction: str) -> str:
		"""
		Attempt to transcribe text from images using the vision-instruct model.
		Note: Exact watsonx multimodal payloads may vary by deployment; if this
		request fails at runtime, callers should catch and fallback to OCR.
		"""
		token = self._ensure_token()
		url = f"{self.settings.watsonx.url.rstrip('/')}/ml/v1/text/generation?version=2023-05-29"
		# Encode images to base64 to pass as part of input context if backend allows.
		encoded_images = [base64.b64encode(img).decode("utf-8") for img in images]
		prompt = (
			"You are a receipt OCR engine. Transcribe the receipt exactly as printed.\n"
			"Return ONLY the transcribed text. No explanations. No markdown.\n"
			"If illegible, use '?' for characters.\n"
			"Images (base64):\n" + "\n".join(f"[IMAGE_BASE64]: {b64[:256]}..." for b64 in encoded_images) + "\n\n"
			+ instruction
		)
		payload: Dict[str, Any] = {
			"model_id": self.model_id,
			"project_id": self.settings.watsonx.project_id,
			"input": prompt,
			"parameters": {
				"decoding_method": "greedy",
				"temperature": self.temperature,
				"max_new_tokens": self.max_tokens,
			},
		}
		headers = {
			"Authorization": f"Bearer {token}",
			"Content-Type": "application/json",
			"Accept": "application/json",
		}
		resp = requests.post(url, headers=headers, json=payload, timeout=45)
		resp.raise_for_status()
		data = resp.json()
		results = data.get("results") or []
		if isinstance(results, list) and results:
			text = results[0].get("generated_text") or results[0].get("output_text")
			if text:
				return str(text).strip()
		return str(data) 