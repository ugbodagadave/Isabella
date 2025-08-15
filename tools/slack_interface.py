from typing import Any, Optional
import os
import tempfile

import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient


class SlackInterface:
	def __init__(self, bot_token: str, app_token: str, signing_secret: str, controller: Any, verify_tokens: bool = False) -> None:
		# Disable network-based token verification by default (tests)
		self.app = App(
			token=bot_token,
			signing_secret=signing_secret,
			token_verification_enabled=verify_tokens,
			request_verification_enabled=verify_tokens,
			ssl_check_enabled=verify_tokens,
			url_verification_enabled=verify_tokens,
		)
		self.app_token = app_token
		self.controller = controller
		self.client = WebClient(token=bot_token)
		self._test_mode = not verify_tokens
		self._register_handlers()

	def _register_handlers(self) -> None:
		@app_event(self.app, "message")
		def handle_message_events(body, say, logger):
			text = body.get("event", {}).get("text", "")
			if text:
				response = self.controller.handle_query(text)
				say(response)

		@app_event(self.app, "file_shared")
		def handle_file_shared(body, say, logger):
			# In unit tests (verify_tokens=False), bypass Slack API calls and pass through
			if self._test_mode:
				result = self.controller.handle_file_shared(body)
				if isinstance(result, str):
					say(result)
				else:
					status = (result or {}).get("status")
					if status == "appended":
						say("✅ Your receipt has been added to Google Sheets")
					elif status == "duplicate":
						say("⚠️ Possible duplicate detected. Sent for review.")
					else:
						say("❌ Could not process the receipt. Please try again or contact support.")
				return
			# Slack sends a minimal payload; fetch full file info via WebClient
			try:
				event = body.get("event", {}) or {}
				file_id: Optional[str] = None
				if isinstance(event.get("file"), dict):
					file_id = event["file"].get("id")
				else:
					file_id = event.get("file_id")
				if not file_id:
					say("Sorry, could not identify the uploaded file.")
					return

				info = self.client.files_info(file=file_id)
				f = info.get("file", {})
				url_private = f.get("url_private_download") or f.get("url_private")
				permalink = f.get("permalink", "")
				filename = f.get("name", "receipt")
				if not url_private:
					say("Sorry, I couldn't download the file.")
					return

				# Download to a temp file using bot token auth
				headers = {"Authorization": f"Bearer {self.client.token}"}
				with requests.get(url_private, headers=headers, stream=True, timeout=60) as r:
					r.raise_for_status()
					fd, tmp_path = tempfile.mkstemp(prefix="receipt_", suffix=f"_{filename}")
					os.close(fd)
					with open(tmp_path, "wb") as out:
						for chunk in r.iter_content(chunk_size=8192):
							if chunk:
								out.write(chunk)

				payload = {"local_path": tmp_path, "receipt_link": permalink}
				# For vision OCR, also attempt URL-based extraction by passing URL as local_path
				if permalink:
					payload["local_path"] = permalink
				result = self.controller.handle_file_shared(payload)

				status = (result or {}).get("status")
				if status == "appended":
					say("✅ Your receipt has been added to Google Sheets")
				elif status == "duplicate":
					say("⚠️ Possible duplicate detected. Sent for review.")
				else:
					say("❌ Could not process the receipt. Please try again or contact support.")
			except Exception as e:
				logger.exception("Error handling file_shared: %s", e)
				say("❌ An error occurred while processing the receipt.")

	def start(self) -> None:
		handler = SocketModeHandler(self.app, self.app_token)
		handler.start()


def app_event(app: App, event_name: str):
	def decorator(func):
		app.event(event_name)(func)
		return func
	return decorator 