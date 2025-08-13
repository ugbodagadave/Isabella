from typing import Any, Dict

from config.prompts import RECEIPT_EXTRACTION_PROMPT


class ReceiptProcessor:
	def __init__(self, granite_client: Any) -> None:
		self.granite = granite_client

	def process(self, receipt_text: str) -> Dict[str, Any]:
		prompt = RECEIPT_EXTRACTION_PROMPT.format(receipt_text=receipt_text)
		response_text = self.granite.generate(prompt)
		return self.granite.parse_json(response_text) 