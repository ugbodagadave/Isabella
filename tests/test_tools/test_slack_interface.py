from unittest.mock import patch

from tools.slack_interface import SlackInterface


class FakeApp:
	def __init__(self, *args, **kwargs):
		self.handlers = {}
		self.logger = None

	def event(self, event_name):
		def register(func):
			self.handlers.setdefault(event_name, []).append(func)
			return func
		return register


def test_slack_interface_handlers_invocation():
	class DummyController:
		def __init__(self):
			self.queries = []
			self.files = []
		def handle_query(self, text):
			self.queries.append(text)
			return "ok"
		def handle_file_shared(self, body):
			self.files.append(body)
			return "processed"

	with patch("tools.slack_interface.App", FakeApp):
		iface = SlackInterface(bot_token="x", app_token="y", signing_secret="z", controller=DummyController(), verify_tokens=False)
		assert hasattr(iface, "start")
		app = iface.app

		# Simulate message event
		message_event = {"event": {"type": "message", "text": "report last month"}}
		handlers = app.handlers.get("message", [])
		assert handlers, "message handler not registered"
		# fake say callable
		class DummySay:
			def __init__(self):
				self.last = None
			def __call__(self, msg):
				self.last = msg
		say = DummySay()
		for h in handlers:
			h(body=message_event, say=say, logger=None)
		assert say.last == "ok"

		# Simulate file_shared event
		file_event = {"event": {"type": "file_shared", "file_id": "F123"}}
		file_handlers = app.handlers.get("file_shared", [])
		assert file_handlers, "file_shared handler not registered"
		say = DummySay()
		for h in file_handlers:
			h(body=file_event, say=say, logger=None)
		assert say.last == "processed" 