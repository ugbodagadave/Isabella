from unittest.mock import patch, MagicMock, mock_open

from integrations.slack_api import SlackApi


def test_slack_api_post_message():
	with patch("integrations.slack_api.WebClient") as MockClient:
		instance = MockClient.return_value
		instance.chat_postMessage = MagicMock(return_value={"ok": True, "ts": "123.456"})

		api = SlackApi(bot_token="x")
		resp = api.post_message(channel="C123", text="hello")
		assert resp["ok"] is True
		instance.chat_postMessage.assert_called_once_with(channel="C123", text="hello")


def test_slack_api_upload_file():
	with patch("integrations.slack_api.WebClient") as MockClient:
		instance = MockClient.return_value
		instance.files_upload_v2 = MagicMock(return_value={"ok": True})
		api = SlackApi(bot_token="x")
		with patch("builtins.open", mock_open(read_data=b"data")) as m:
			resp = api.upload_file(channel="C123", file_path="/tmp/a.txt", title="A")
			assert resp["ok"] is True
			instance.files_upload_v2.assert_called_once() 