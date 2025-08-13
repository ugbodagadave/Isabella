from typing import Optional
from pathlib import Path
import logging

import pytesseract
from PIL import Image, ImageOps, ImageFilter
import pdfplumber


logger = logging.getLogger(__name__)


class TextExtractor:
	def __init__(self, tesseract_cmd: Optional[str] = None, lang: str = "eng") -> None:
		if tesseract_cmd:
			pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
		self.lang = lang

	def _preprocess_image(self, image: Image.Image) -> Image.Image:
		# Simple, optional preprocessing: grayscale + contrast + sharpen
		try:
			gray = ImageOps.grayscale(image)
			sharpened = gray.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
			return sharpened
		except Exception as e:
			logger.debug("Image preprocessing failed; proceeding without preprocessing: %s", str(e))
			return image

	def extract_from_image(self, image_path: str) -> str:
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
		ext = ""
		extension = Path(path).suffix.lower()
		if extension in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}:
			text = self.extract_from_image(path)
		elif extension == ".pdf":
			text = self.extract_from_pdf(path)
		else:
			raise ValueError(f"Unsupported file type: {extension}")
		return text 