import pytest

from models.granite_client import GraniteClient


def test_granite_build_request_structure():
	gc = GraniteClient()
	payload = gc.build_request("hello", temperature=0.2, max_tokens=256)
	assert payload["model_id"] == gc.settings.watsonx.model_id
	assert payload["input"] == "hello"
	assert payload["parameters"]["temperature"] == 0.2
	assert payload["parameters"]["max_tokens"] == 256


def test_granite_generate_raises_not_implemented():
	gc = GraniteClient()
	with pytest.raises(NotImplementedError):
		_ = gc.generate("prompt") 