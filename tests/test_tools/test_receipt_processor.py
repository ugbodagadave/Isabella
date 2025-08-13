from typing import Any
import json
import pytest

from tools.receipt_processor import ReceiptProcessor


class DummyGranite:
	def __init__(self, response_text: str):
		self.response_text = response_text
		self.last_prompt = None

	def generate(self, prompt: str) -> str:
		self.last_prompt = prompt
		return self.response_text

	def parse_json(self, text: str):
		return json.loads(text)


def test_receipt_processor_flow_valid():
	valid_json = json.dumps({
		"vendor": "ACME",
		"amount": 12.34,
		"date": "2024-01-01",
		"category": "Office Supplies"
	})
	client = DummyGranite(valid_json)
	rp = ReceiptProcessor(client)
	result = rp.process("Total $12.34 at ACME 2024-01-01")
	assert result["vendor"] == "ACME"
	assert "RECEIPT TEXT" in client.last_prompt


def test_receipt_processor_invalid_json_raises():
	client = DummyGranite("not-json")
	rp = ReceiptProcessor(client)
	with pytest.raises(ValueError):
		_ = rp.process("text")


def test_receipt_processor_schema_validation_fails():
	# Missing required 'vendor'
	invalid = json.dumps({
		"amount": 10,
		"date": "2024-01-01",
		"category": "Other Business Expenses"
	})
	client = DummyGranite(invalid)
	rp = ReceiptProcessor(client)
	with pytest.raises(Exception):
		_ = rp.process("text") 