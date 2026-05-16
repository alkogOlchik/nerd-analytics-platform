from __future__ import annotations

import os
from pathlib import Path

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma4:e4b"
OLLAMA_CTX_SIZE = 20000
BROWSER_HEADLESS = False
BROWSER_MAX_ACTIONS_PER_STEP = int(os.getenv("BROWSER_MAX_ACTIONS_PER_STEP", "3"))
OUTPUT_DIR = "output"
SCREENSHOT_QUALITY = 85
MAX_STEPS = 50
STEP_TIMEOUT_SECONDS = int(os.getenv("STEP_TIMEOUT_SECONDS", "90"))

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / OUTPUT_DIR
SCREENSHOTS_PATH = OUTPUT_PATH / "screenshots"
GUIDES_PATH = OUTPUT_PATH / "guides"
