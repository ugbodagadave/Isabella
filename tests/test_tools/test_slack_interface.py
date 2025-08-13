from tools.slack_interface import SlackInterface


def test_slack_interface_import_only():
	# We won't start the app; just ensure class can be constructed with dummies
	class DummyController:
		def handle_query(self, text):
			return "ok"
		def handle_file_shared(self, body):
			return "processed"

	iface = SlackInterface(bot_token="x", app_token="y", signing_secret="z", controller=DummyController(), verify_tokens=False)
	assert hasattr(iface, "start") 