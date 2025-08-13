from unittest.mock import patch, MagicMock

from tools.text_extractor import TextExtractor


def test_text_extractor_init():
	tex = TextExtractor(tesseract_cmd="/usr/bin/tesseract", lang="eng")
	assert tex.lang == "eng"


@patch("tools.text_extractor.pytesseract.image_to_string", return_value="Hello World\n")
@patch("tools.text_extractor.Image.open")
def test_extract_from_image(mock_open, mock_ocr):
	mock_img = MagicMock()
	mock_open.return_value = mock_img
	tex = TextExtractor(lang="eng")
	text = tex.extract_from_image("/tmp/sample.png")
	assert text == "Hello World"
	mock_ocr.assert_called_once()


@patch("tools.text_extractor.pdfplumber.open")
def test_extract_from_pdf(mock_pdf_open):
	# Mock a PDF with two pages, one with text and one empty
	mock_page1 = MagicMock()
	mock_page1.extract_text.return_value = "Page 1 Text"
	mock_page2 = MagicMock()
	mock_page2.extract_text.return_value = None

	mock_pdf = MagicMock()
	mock_pdf.__enter__.return_value = mock_pdf
	mock_pdf.pages = [mock_page1, mock_page2]
	mock_pdf_open.return_value = mock_pdf

	tex = TextExtractor()
	text = tex.extract_from_pdf("/tmp/sample.pdf")
	assert text == "Page 1 Text"
	mock_pdf_open.assert_called_once() 