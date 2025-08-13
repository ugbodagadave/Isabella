from tools.receipt_processor import ReceiptProcessor


class DummyGranite:
	def __init__(self, response_text: str):
		self.response_text = response_text
		self.last_prompt = None

	def generate(self, prompt: str) -> str:
		self.last_prompt = prompt
		return self.response_text

	def parse_json(self, text: str):
		return {"vendor": "ACME", "amount": 12.34, "date": "2024-01-01", "category": "Office Supplies"}


def test_receipt_processor_flow():
	client = DummyGranite("{}")
	rp = ReceiptProcessor(client)
	result = rp.process("Total $12.34 at ACME 2024-01-01")
	assert result["vendor"] == "ACME"
	assert "RECEIPT TEXT" in client.last_prompt 