from __future__ import annotations

from typing import List
from pathlib import Path
import io

from PIL import Image
import pdfplumber

from models.vision_client import VisionClient

# Inline configuration for this phase (non-secret values)
OCR_BACKEND = "vision"  # default here; runner will choose dynamically
VISION_MODEL_ID = "ibm/granite-llama-3-2-11b-vision-instruct"
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
		# Downscale if needed
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

	def extract(self, path: str) -> str:
		ext = Path(path).suffix.lower()
		images: List[bytes]
		if ext == ".pdf":
			images = self._pdf_to_images(path)
		else:
			img = Image.open(path)
			images = [self._image_to_bytes(img)]
		instruction = (
			"Transcribe all visible text from the attached receipt image(s).\n"
			"Preserve line breaks, spacing for amounts, and currency symbols.\n"
			"Return only the transcribed text."
		)
		return self.client.transcribe(images, instruction) 