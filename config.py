from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv(override=False)
APP_NAME = "ShopSense AI"
MAX_UPLOAD_MB = int(os.getenv("SHOPSENSE_MAX_UPLOAD_MB", "5"))
MAX_ROWS = int(os.getenv("SHOPSENSE_MAX_ROWS", "50000"))
MAX_QUESTION_CHARS = 1000
LLM_API_KEY = os.getenv("SHOPSENSE_LLM_API_KEY", "").strip()
LLM_MODEL = os.getenv("SHOPSENSE_LLM_MODEL", "").strip()
LLM_BASE_URL = os.getenv("SHOPSENSE_LLM_BASE_URL", "").strip() or None
LLM_TIMEOUT_SECONDS = float(os.getenv("SHOPSENSE_LLM_TIMEOUT_SECONDS", "15"))
