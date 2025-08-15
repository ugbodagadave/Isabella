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

	@staticmethod
	def _parse_chat_text(data: Dict[str, Any]) -> Optional[str]:
		"""Try multiple known result shapes to extract generated text from chat response."""
		try:
			# 1) Standard: results[0].generated_text or output_text
			results = data.get("results") or []
			if isinstance(results, list) and results:
				cand = results[0].get("generated_text") or results[0].get("output_text")
				if cand:
					return str(cand).strip()
				# 2) Nested message content: results[0].message.content -> list of {type,text}
				msg = results[0].get("message") or {}
				content = msg.get("content") or []
				if isinstance(content, list):
					texts = []
					for part in content:
						if isinstance(part, dict):
							val = part.get("text") or part.get("output_text") or part.get("generated_text")
							if isinstance(val, str) and val.strip():
								texts.append(val.strip())
					if texts:
						return "\n".join(texts)
			# 3) Top-level output fields
			for key in ("generated_text", "output_text", "text"):
				val = data.get(key)
				if isinstance(val, str) and val.strip():
					return val.strip()
		except Exception:
			return None
		return None

	def transcribe(self, images: List[bytes], instruction: str) -> str:
		"""
		Transcribe text from images using the chat multimodal endpoint with correct content types.
		- Uses content parts: {"type":"text"} and {"type":"image_url"}
		- Embeds the image via data URI in image_url
		If a valid chat response is not parsed, returns an empty string so callers can treat as insufficient.
		"""
		token = self._ensure_token()
		base_url = self.settings.watsonx.url.rstrip('/')
		chat_url = f"{base_url}/ml/v1/text/chat?version=2023-05-29"
		# Build messages: system + user (image(s) + instruction)
		system_msg = {
			"role": "system",
			"content": (
				"You are a receipt OCR engine. Transcribe the receipt exactly as printed. "
				"Return ONLY the transcribed text. No explanations. No markdown. "
				"If illegible, use '?' for characters."
			),
		}
		user_content: List[Dict[str, Any]] = []
		for img in images:
			b64 = base64.b64encode(img).decode("utf-8")
			user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
		user_content.append({"type": "text", "text": instruction})
		user_msg = {"role": "user", "content": user_content}
		payload: Dict[str, Any] = {
			"model_id": self.model_id,
			"project_id": self.settings.watsonx.project_id,
			"messages": [system_msg, user_msg],
			"temperature": self.temperature,
			"max_tokens": self.max_tokens,
			"top_p": 1,
			"frequency_penalty": 0,
			"presence_penalty": 0,
		}
		try:
			resp = requests.post(chat_url, headers=self._headers(token), json=payload, timeout=60)
			if resp.status_code >= 400:
				logger.warning("Vision chat HTTP %s: %s", resp.status_code, resp.text[:500])
			resp.raise_for_status()
			data = resp.json()
			text = self._parse_chat_text(data)
			if text:
				return text
			logger.warning("Vision chat response parsed no text; keys=%s", ",".join(list(data.keys())[:10]))
		except Exception as e:
			logger.warning("Vision chat endpoint failed: %s", e)
		# Do NOT fallback to text-generation with base64 markers; return empty to signal insufficiency
		return ""


	def transcribe_urls(self, image_urls: List[str], instruction: str) -> str:
		"""
		Transcribe text from one or more publicly accessible image URLs using chat API.
		Returns empty string if parsing fails.
		"""
		token = self._ensure_token()
		base_url = self.settings.watsonx.url.rstrip('/')
		chat_url = f"{base_url}/ml/v1/text/chat?version=2023-05-29"
		system_msg = {
			"role": "system",
			"content": (
				"You are a receipt OCR engine. Transcribe the receipt exactly as printed. "
				"Return ONLY the transcribed text. No explanations. No markdown. "
				"If illegible, use '?' for characters."
			),
		}
		user_content: List[Dict[str, Any]] = []
		for url in image_urls:
			user_content.append({"type": "image_url", "image_url": {"url": url}})
		user_content.append({"type": "text", "text": instruction})
		payload: Dict[str, Any] = {
			"model_id": self.model_id,
			"project_id": self.settings.watsonx.project_id,
			"messages": [system_msg, {"role": "user", "content": user_content}],
			"temperature": self.temperature,
			"max_tokens": self.max_tokens,
			"top_p": 1,
			"frequency_penalty": 0,
			"presence_penalty": 0,
		}
		resp = requests.post(chat_url, headers=self._headers(token), json=payload, timeout=60)
		if resp.status_code >= 400:
			logger.warning("Vision chat HTTP %s: %s", resp.status_code, resp.text[:500])
		resp.raise_for_status()
		data = resp.json()
		text = self._parse_chat_text(data)
		return text or "" 