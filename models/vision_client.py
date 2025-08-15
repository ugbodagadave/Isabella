import base64
import logging
import time
from typing import Any, Dict, List, Optional

import requests

from config.settings import load_settings


logger = logging.getLogger(__name__)


class VisionClient:
	"""
	Thin client for IBM watsonx multimodal (vision-instruct) models using the chat API.
	Sends images as base64 in message content. Falls back to text-generation if chat is unavailable.
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

	def _headers(self, token: str) -> Dict[str, str]:
		return {
			"Authorization": f"Bearer {token}",
			"Content-Type": "application/json",
			"Accept": "application/json",
		}

	def transcribe(self, images: List[bytes], instruction: str) -> str:
		"""
		Transcribe text from images using the chat multimodal endpoint.
		Falls back to text-generation if chat is not available.
		"""
		token = self._ensure_token()
		base_url = self.settings.watsonx.url.rstrip('/')
		chat_url = f"{base_url}/ml/v1/text/chat?version=2023-05-29"
		# Build chat-style messages with input_text + input_image parts
		contents: List[Dict[str, Any]] = [{"type": "input_text", "text": instruction}]
		for img in images:
			b64 = base64.b64encode(img).decode("utf-8")
			contents.append({
				"type": "input_image",
				"mime_type": "image/jpeg",
				"data": b64,
			})
		payload: Dict[str, Any] = {
			"model_id": self.model_id,
			"project_id": self.settings.watsonx.project_id,
			"messages": [{"role": "user", "content": contents}],
			"parameters": {
				"decoding_method": "greedy",
				"temperature": self.temperature,
				"max_new_tokens": self.max_tokens,
			},
		}
		try:
			resp = requests.post(chat_url, headers=self._headers(token), json=payload, timeout=60)
			resp.raise_for_status()
			data = resp.json()
			results = data.get("results") or []
			if isinstance(results, list) and results:
				text = results[0].get("generated_text") or results[0].get("output_text")
				if text:
					return str(text).strip()
		except Exception as e:
			logger.warning("Vision chat endpoint failed; falling back to text-generation: %s", e)
		# Fallback to text-generation with a compact inline base64 summary (best-effort)
		gen_url = f"{base_url}/ml/v1/text/generation?version=2023-05-29"
		encoded_images = [base64.b64encode(img).decode("utf-8") for img in images]
		prompt = (
			"You are a receipt OCR engine. Transcribe the receipt exactly as printed.\n"
			"Return ONLY the transcribed text. No explanations. No markdown.\n"
			"For each image below (base64), read and transcribe.\n"
			+ "\n".join(f"[IMAGE_BASE64_BEGIN]{b64[:2048]}[...trimmed]" for b64 in encoded_images)
		)
		gen_payload: Dict[str, Any] = {
			"model_id": self.model_id,
			"project_id": self.settings.watsonx.project_id,
			"input": prompt,
			"parameters": {
				"decoding_method": "greedy",
				"temperature": self.temperature,
				"max_new_tokens": self.max_tokens,
			},
		}
		resp = requests.post(gen_url, headers=self._headers(token), json=gen_payload, timeout=60)
		resp.raise_for_status()
		data = resp.json()
		results = data.get("results") or []
		if isinstance(results, list) and results:
			text = results[0].get("generated_text") or results[0].get("output_text")
			if text:
				return str(text).strip()
		return str(data) 