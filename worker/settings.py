""" carregamento de configuração a partir do ambiente """

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from worker.constants import DEFAULT_SCHEDULE_TIMES


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_key: str
    airlabs_api_key: str
    airport_iata: str
    timezone_name: str
    schedule_times: tuple[str, ...]
    run_on_start: bool
    airlabs_limit: int

    @property
    def timezone(self) -> ZoneInfo:
        return ZoneInfo(self.timezone_name)


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "sim"}


def parse_schedule_times(raw_value: str) -> tuple[str, ...]:
    times = tuple(item.strip() for item in raw_value.split(",") if item.strip())
    if not times:
        raise ValueError("SCHEDULE_TIMES não pode estar vazio")

    for item in times:
        try:
            datetime.strptime(item, "%H:%M")
        except ValueError as exc:
            raise ValueError(f"Hora inválida em SCHEDULE_TIMES: {item}. Usa HH:MM") from exc

    return times


def load_dotenv_if_present() -> None:
    load_dotenv()


def load_supabase_credentials() -> tuple[str, str]:
    """Só URL + key (útil para --reset-table sem exigir Airlabs)."""
    load_dotenv_if_present()
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_KEY", "").strip()
    if not url or not key:
        raise RuntimeError("SUPABASE_URL e SUPABASE_KEY são obrigatórios.")
    return url, key


def load_settings() -> Settings:
    load_dotenv_if_present()

    required = {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY"),
        "AIRLABS_API_KEY": os.getenv("AIRLABS_API_KEY"),
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"Variáveis de ambiente em falta: {', '.join(missing)}")

    raw_schedule = os.getenv("SCHEDULE_TIMES", DEFAULT_SCHEDULE_TIMES)
    if not isinstance(raw_schedule, str):
        raise RuntimeError("SCHEDULE_TIMES tem de ser texto (ex.: 06:00,18:00)")

    return Settings(
        supabase_url=required["SUPABASE_URL"].strip(),
        supabase_key=required["SUPABASE_KEY"].strip(),
        airlabs_api_key=required["AIRLABS_API_KEY"].strip(),
        airport_iata=os.getenv("AIRPORT_IATA", "OPO").strip().upper(),
        timezone_name=os.getenv("WORKER_TIMEZONE", "Europe/Lisbon").strip(),
        schedule_times=parse_schedule_times(raw_schedule),
        run_on_start=parse_bool(os.getenv("RUN_ON_START"), default=True),
        airlabs_limit=max(1, int(os.getenv("AIRLABS_LIMIT", "1000"))),
    )


def setup_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
