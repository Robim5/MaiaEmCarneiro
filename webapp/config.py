""" caminhos e leitura mínima de ambiente para o dashboard """

from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

WEBAPP_DIR = Path(__file__).resolve().parent
REPO_ROOT = WEBAPP_DIR.parent
ASSETS_DIR = REPO_ROOT / "assets"
LOGO_FILE = ASSETS_DIR / "logo.png"


def get_timezone_name() -> str:
    return (os.getenv("WORKER_TIMEZONE") or "Europe/Lisbon").strip()


def today_in_app_tz() -> date:
    return datetime.now(ZoneInfo(get_timezone_name())).date()


def supabase_credentials() -> tuple[str, str]:
    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_KEY") or "").strip()
    if not url or not key:
        raise RuntimeError("SUPABASE_URL e SUPABASE_KEY são obrigatórios no .env.")
    return url, key
