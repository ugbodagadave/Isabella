from typing import Any

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler


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
			# Placeholder: controller is expected to fetch the file and process
			result = self.controller.handle_file_shared(body)
			say(result)

	def start(self) -> None:
		handler = SocketModeHandler(self.app, self.app_token)
		handler.start()


def app_event(app: App, event_name: str):
	def decorator(func):
		app.event(event_name)(func)
		return func
	return decorator 