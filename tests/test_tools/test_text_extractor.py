from tools.text_extractor import TextExtractor


def test_text_extractor_init():
	tex = TextExtractor(tesseract_cmd="/usr/bin/tesseract", lang="eng")
	assert tex.lang == "eng" 