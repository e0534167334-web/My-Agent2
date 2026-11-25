from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import os
from pathlib import Path
load_dotenv()
TIMEZONE = ZoneInfo('Asia/Jerusalem')
MAX_PLAN_RETRIES = 2
DATA = Path(__file__).resolve().parent / 'data'
DATA.mkdir(exist_ok=True)
MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
