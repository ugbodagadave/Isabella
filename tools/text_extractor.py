from typing import Optional
from pathlib import Path
import logging
import os
import io

import pytesseract
from PIL import Image, ImageOps, ImageFilter
import pdfplumber

from models.vision_client import VisionClient


logger = logging.getLogger(__name__)


# Inline vision defaults (non-secret)
VISION_MODEL_ID = "meta-llama/llama-3-2-11b-vision-instruct"
VISION_TEMPERATURE = 0.0
VISION_MAX_TOKENS = 2048
VISION_PAGE_LIMIT = 4
VISION_IMAGE_MAX_DIM = 2048


class TextExtractor:
	def __init__(self, tesseract_cmd: Optional[str] = None, lang: str = "eng", backend: Optional[str] = None) -> None:
		if tesseract_cmd:
			pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
		self.lang = lang
		self.backend = (backend or os.getenv("OCR_BACKEND", "vision")).strip().lower()
		self._vision: Optional[VisionClient] = None
		if self.backend == "vision":
			self._vision = VisionClient(
				model_id=VISION_MODEL_ID,
				temperature=VISION_TEMPERATURE,
				max_tokens=VISION_MAX_TOKENS,
			)

	def _preprocess_image(self, image: Image.Image) -> Image.Image:
		# Simple, optional preprocessing: grayscale + contrast + sharpen (used only for tesseract backend)
		try:
			gray = ImageOps.grayscale(image)
			sharpened = gray.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
			return sharpened
		except Exception as e:
			logger.debug("Image preprocessing failed; proceeding without preprocessing: %s", str(e))
			return image

	def _image_to_bytes(self, image: Image.Image) -> bytes:
		w, h = image.size
		max_dim = max(w, h)
		if max_dim > VISION_IMAGE_MAX_DIM:
			scale = VISION_IMAGE_MAX_DIM / float(max_dim)
			image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
		buf = io.BytesIO()
		image.save(buf, format="JPEG", quality=85, optimize=True)
		return buf.getvalue()

	def _pdf_to_images(self, pdf_path: str) -> list[bytes]:
		images: list[bytes] = []
		with pdfplumber.open(pdf_path) as pdf:
			for page in pdf.pages[:VISION_PAGE_LIMIT]:
				pil = page.to_image(resolution=300).original
				images.append(self._image_to_bytes(pil))
		return images

	def _vision_transcribe_images(self, images: list[bytes], instruction: str) -> str:
		assert self._vision is not None, "Vision client not initialized"
		return self._vision.transcribe(images, instruction)

	def _vision_transcribe_urls(self, urls: list[str], instruction: str) -> str:
		assert self._vision is not None, "Vision client not initialized"
		return self._vision.transcribe_urls(urls, instruction)

	def extract_from_image(self, image_path: str) -> str:
		if self.backend == "vision":
			img = Image.open(image_path)
			images = [self._image_to_bytes(img)]
			instruction = (
				"Transcribe all visible text from the attached receipt image.\n"
				"Preserve line breaks, spacing for amounts, and currency symbols.\n"
				"Return only the transcribed text."
			)
			text = self._vision_transcribe_images(images, instruction)
			return (text or "").strip()
		# tesseract path (legacy)
		try:
			image = Image.open(image_path)
			image = self._preprocess_image(image)
			text = pytesseract.image_to_string(image, lang=self.lang)
			return text.strip()
		except FileNotFoundError:
			raise
		except Exception as e:
			logger.error("OCR extraction failed for %s: %s", image_path, str(e))
			raise

	def extract_from_pdf(self, pdf_path: str) -> str:
		if self.backend == "vision":
			images = self._pdf_to_images(pdf_path)
			instruction = (
				"Transcribe all visible text from the attached receipt image(s).\n"
				"Preserve line breaks, spacing for amounts, and currency symbols.\n"
				"Return only the transcribed text."
			)
			text = self._vision_transcribe_images(images, instruction)
			return (text or "").strip()
		# legacy pdf text extraction path
		texts = []
		try:
			with pdfplumber.open(pdf_path) as pdf:
				for page in pdf.pages:
					texts.append(page.extract_text(x_tolerance=2, y_tolerance=2) or "")
			return "\n".join(t.strip() for t in texts if t).strip()
		except FileNotFoundError:
			raise
		except Exception as e:
			logger.error("PDF text extraction failed for %s: %s", pdf_path, str(e))
			raise

	def extract(self, path: str) -> str:
		# URL handling for vision backend
		if self.backend == "vision" and (path.lower().startswith("http://") or path.lower().startswith("https://")):
			instruction = (
				"Transcribe all visible text from the receipt image.\n"
				"Preserve line breaks and amounts. Return only the transcribed text."
			)
			text = self._vision_transcribe_urls([path], instruction)
			return (text or "").strip()
		ext = ""
		extension = Path(path).suffix.lower()
		if extension in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}:
			text = self.extract_from_image(path)
		elif extension == ".pdf":
			text = self.extract_from_pdf(path)
		else:
			raise ValueError(f"Unsupported file type: {extension}")
		return text 