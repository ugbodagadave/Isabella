import pytest
from unittest.mock import patch, MagicMock

from models.granite_client import GraniteClient


def test_granite_build_request_structure():
	gc = GraniteClient()
	payload = gc.build_request("hello", temperature=0.2, max_tokens=256)
	assert payload["model_id"] == gc.settings.watsonx.model_id
	assert payload["input"] == "hello"
	assert payload["parameters"]["temperature"] == 0.2
	assert payload["parameters"]["max_new_tokens"] == 256


def test_granite_generate_returns_text():
	gc = GraniteClient()
	with patch.object(GraniteClient, "_ensure_token", return_value="token"), \
		 patch("models.granite_client.requests.post") as mock_post:
		resp = MagicMock()
		resp.json.return_value = {"results": [{"generated_text": "{}"}]}
		resp.raise_for_status.return_value = None
		mock_post.return_value = resp
		text = gc.generate("prompt")
		assert text == "{}" 