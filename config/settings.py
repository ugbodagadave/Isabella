import os
from dataclasses import dataclass
from typing import Optional


def getenv_bool(key: str, default: bool = False) -> bool:
	value = os.getenv(key)
	if value is None:
		return default
	return str(value).strip().lower() in {"1", "true", "yes", "on"}


def getenv_int(key: str, default: int) -> int:
	try:
		return int(os.getenv(key, default))
	except ValueError:
		return default


@dataclass
class WatsonxConfig:
	api_key: str
	project_id: str
	url: str
	model_id: str


@dataclass
class GoogleSheetsConfig:
	credentials_path: str
	spreadsheet_id: str
	worksheet_name: str


@dataclass
class SlackConfig:
	bot_token: str
	app_token: str
	signing_secret: str
	default_channel_id: Optional[str] = None


@dataclass
class OcrConfig:
	tesseract_cmd: str
	tesseract_lang: str = "eng"
	ocr_confidence_threshold: int = 70
	image_preprocessing: bool = True


@dataclass
class BusinessRules:
	default_currency: str = "USD"
	timezone: str = "America/New_York"
	auto_categorization_enabled: bool = True
	duplicate_detection_enabled: bool = True
	require_approval: bool = False


@dataclass
class Settings:
	watsonx: WatsonxConfig
	google_sheets: GoogleSheetsConfig
	slack: SlackConfig
	ocr: OcrConfig
	rules: BusinessRules
	file_storage_type: Optional[str] = None
	database_url: Optional[str] = None


def load_settings() -> Settings:
	# Note: We do not read files; we only reference environment variables.
	watsonx = WatsonxConfig(
		api_key=os.getenv("WATSONX_API_KEY", ""),
		project_id=os.getenv("WATSONX_PROJECT_ID", ""),
		url=os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
		model_id=os.getenv("GRANITE_MODEL_ID", "ibm/granite-3.3-8b-instruct"),
	)

	google = GoogleSheetsConfig(
		credentials_path=os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "./config/google-credentials.json"),
		spreadsheet_id=os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", ""),
		worksheet_name=os.getenv("GOOGLE_SHEETS_WORKSHEET_NAME", "Expenses"),
	)

	slack = SlackConfig(
		bot_token=os.getenv("SLACK_BOT_TOKEN", ""),
		app_token=os.getenv("SLACK_APP_TOKEN", ""),
		signing_secret=os.getenv("SLACK_SIGNING_SECRET", ""),
		default_channel_id=os.getenv("SLACK_CHANNEL_ID"),
	)

	ocr = OcrConfig(
		tesseract_cmd=os.getenv("TESSERACT_CMD", ""),
		tesseract_lang=os.getenv("TESSERACT_LANG", "eng"),
		ocr_confidence_threshold=getenv_int("OCR_CONFIDENCE_THRESHOLD", 70),
		image_preprocessing=getenv_bool("IMAGE_PREPROCESSING", True),
	)

	rules = BusinessRules(
		default_currency=os.getenv("DEFAULT_CURRENCY", "USD"),
		timezone=os.getenv("TIMEZONE", "America/New_York"),
		auto_categorization_enabled=getenv_bool("AUTO_CATEGORIZATION_ENABLED", True),
		duplicate_detection_enabled=getenv_bool("DUPLICATE_DETECTION_ENABLED", True),
		require_approval=getenv_bool("REQUIRE_APPROVAL", False),
	)

	return Settings(
		watsonx=watsonx,
		google_sheets=google,
		slack=slack,
		ocr=ocr,
		rules=rules,
		file_storage_type=os.getenv("FILE_STORAGE_TYPE"),
		database_url=os.getenv("DATABASE_URL"),
	) 