from typing import Any

from slack_sdk import WebClient


class SlackApi:
	def __init__(self, bot_token: str) -> None:
		self.client = WebClient(token=bot_token)

	def post_message(self, channel: str, text: str) -> Any:
		return self.client.chat_postMessage(channel=channel, text=text) 