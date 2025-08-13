from unittest.mock import patch, MagicMock

from integrations.slack_api import SlackApi


def test_slack_api_post_message():
	with patch("integrations.slack_api.WebClient") as MockClient:
		instance = MockClient.return_value
		instance.chat_postMessage = MagicMock(return_value={"ok": True, "ts": "123.456"})

		api = SlackApi(bot_token="x")
		resp = api.post_message(channel="C123", text="hello")
		assert resp["ok"] is True
		instance.chat_postMessage.assert_called_once_with(channel="C123", text="hello") 