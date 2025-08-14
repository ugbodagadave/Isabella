from typing import Any

from slack_sdk import WebClient


class SlackApi:
	def __init__(self, bot_token: str) -> None:
		self.client = WebClient(token=bot_token)

	def post_message(self, channel: str, text: str) -> Any:
		return self.client.chat_postMessage(channel=channel, text=text)

	def upload_file(self, channel: str, file_path: str, title: str | None = None) -> Any:
		with open(file_path, "rb") as f:
			return self.client.files_upload_v2(channels=channel, file=f, title=title or "upload")

	def file_download_url(self, file_id: str) -> str:
		info = self.client.files_info(file=file_id)
		file_obj = (info or {}).get("file") or info.data.get("file")  # type: ignore[attr-defined]
		return file_obj.get("url_private_download") if file_obj else "" 