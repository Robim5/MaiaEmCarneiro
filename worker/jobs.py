""" orquestração do job Airlabs + Supabase """

from __future__ import annotations

import logging
from datetime import datetime

from worker.airlabs import count_daily_airport_movements
from worker.db import (
    cleanup_old_rows,
    get_client,
    recalculate_month_total,
    upsert_daily_rollup,
    upsert_monthly_rollup,
)
from worker.settings import Settings


def run_job(settings: Settings) -> None:
    logging.info("Início do job Airlabs/Supabase")

    supabase = get_client(settings.supabase_url, settings.supabase_key)
    today = datetime.now(settings.timezone).date()
    month_key = today.strftime("%Y-%m")

    flights = count_daily_airport_movements(settings, today)
    upsert_daily_rollup(supabase, today, flights)

    month_total = recalculate_month_total(supabase, month_key)
    upsert_monthly_rollup(supabase, month_key, month_total)

    cleanup_old_rows(supabase, today)
    logging.info("Fim do job Airlabs/Supabase")
