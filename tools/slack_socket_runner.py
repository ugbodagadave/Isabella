from __future__ import annotations

import logging
from pathlib import Path
import os

from dotenv import load_dotenv

from config.settings import load_settings
from integrations.google_sheets_api import GoogleSheetsClient
from models.granite_client import GraniteClient
from tools.controller import Controller
from tools.receipt_processor import ReceiptProcessor
from tools.sheets_manager import SheetsManager
from tools.slack_interface import SlackInterface


def main() -> None:
	# Load environment variables from project root .env
	project_root = Path(__file__).resolve().parents[1]
	load_dotenv(project_root / ".env")

	logging.basicConfig(level=logging.INFO)
	settings = load_settings()

	# Vision-only text extractor
	from tools.vision_text_extractor import VisionTextExtractor
	text_extractor = VisionTextExtractor()

	granite = GraniteClient()
	receipt_processor = ReceiptProcessor(granite)
	gs = GoogleSheetsClient()
	gs.connect()
	sheets_manager = SheetsManager(gs)

	controller = Controller(
		text_extractor=text_extractor,
		receipt_processor=receipt_processor,
		sheets_manager=sheets_manager,
	)

	slack = SlackInterface(
		bot_token=settings.slack.bot_token,
		app_token=settings.slack.app_token,  # Socket Mode
		signing_secret=settings.slack.signing_secret,
		controller=controller,
		verify_tokens=True,
	)
	# Blocking start; run this in a dedicated terminal
	slack.start()


if __name__ == "__main__":
	main() 