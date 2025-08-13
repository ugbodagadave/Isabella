from typing import Optional
from pathlib import Path

import pytesseract
from PIL import Image
import pdfplumber


class TextExtractor:
	def __init__(self, tesseract_cmd: Optional[str] = None, lang: str = "eng") -> None:
		if tesseract_cmd:
			pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
		self.lang = lang

	def extract_from_image(self, image_path: str) -> str:
		image = Image.open(image_path)
		text = pytesseract.image_to_string(image, lang=self.lang)
		return text.strip()

	def extract_from_pdf(self, pdf_path: str) -> str:
		texts = []
		with pdfplumber.open(pdf_path) as pdf:
			for page in pdf.pages:
				texts.append(page.extract_text(x_tolerance=2, y_tolerance=2) or "")
		return "\n".join(t.strip() for t in texts if t).strip()

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