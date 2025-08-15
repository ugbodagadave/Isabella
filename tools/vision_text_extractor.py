from __future__ import annotations

from typing import List, Optional
from pathlib import Path
import io

from PIL import Image
import pdfplumber

from models.vision_client import VisionClient

# Inline configuration for this phase (non-secret values)
OCR_BACKEND = "vision"
VISION_MODEL_ID = "meta-llama/llama-3-2-11b-vision-instruct"
VISION_TEMPERATURE = 0.0
VISION_MAX_TOKENS = 2048
VISION_PAGE_LIMIT = 4
VISION_IMAGE_MAX_DIM = 2048


class VisionTextExtractor:
	def __init__(self) -> None:
		self.client = VisionClient(
			model_id=VISION_MODEL_ID,
			temperature=VISION_TEMPERATURE,
			max_tokens=VISION_MAX_TOKENS,
		)

	def _image_to_bytes(self, image: Image.Image) -> bytes:
		w, h = image.size
		max_dim = max(w, h)
		if max_dim > VISION_IMAGE_MAX_DIM:
			scale = VISION_IMAGE_MAX_DIM / float(max_dim)
			image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
		buf = io.BytesIO()
		image.save(buf, format="JPEG", quality=85, optimize=True)
		return buf.getvalue()

	def _pdf_to_images(self, pdf_path: str) -> List[bytes]:
		images: List[bytes] = []
		with pdfplumber.open(pdf_path) as pdf:
			for idx, page in enumerate(pdf.pages[:VISION_PAGE_LIMIT]):
				pil = page.to_image(resolution=300).original
				images.append(self._image_to_bytes(pil))
		return images

	def extract_from_url(self, url: str) -> str:
		instruction = (
			"Transcribe all visible text from the receipt image.\n"
			"Preserve line breaks and amounts. Return only the transcribed text."
		)
		return self.client.transcribe_urls([url], instruction)

	def extract(self, path_or_url: str) -> str:
		# If it looks like an http(s) URL, use url path
		if path_or_url.lower().startswith("http://") or path_or_url.lower().startswith("https://"):
			return self.extract_from_url(path_or_url)
		ext = Path(path_or_url).suffix.lower()
		images: List[bytes]
		if ext == ".pdf":
			images = self._pdf_to_images(path_or_url)
		else:
			img = Image.open(path_or_url)
			images = [self._image_to_bytes(img)]
		instruction = (
			"Transcribe all visible text from the attached receipt image(s).\n"
			"Preserve line breaks, spacing for amounts, and currency symbols.\n"
			"Return only the transcribed text."
		)
		return self.client.transcribe(images, instruction) 