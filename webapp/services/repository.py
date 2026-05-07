""" leituras Supabase usadas pelo dashboard """

from __future__ import annotations

from typing import Any

from supabase import Client

from worker.constants import TABLE_NAME


def fetch_day_rows_for_month(supabase: Client, month_key: str) -> tuple[list[dict[str, Any]], str | None]:
    """ rollups diários do mês (um mês civil tem no máximo 31 linhas) """
    try:
        res = (
            supabase.table(TABLE_NAME)
            .select("day_date,flights,updated_at,source")
            .eq("entry_type", "day")
            .eq("month_key", month_key)
            .order("day_date", desc=False)
            .execute()
        )
        rows = list(res.data or [])
        rows.sort(key=lambda r: str(r.get("day_date") or ""))
        return rows, None
    except Exception as exc:  # noqa: BLE001
        return [], str(exc)


def fetch_month_rollup_row(supabase: Client, month_key: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        res = (
            supabase.table(TABLE_NAME)
            .select("flights,updated_at,source")
            .eq("entry_type", "month")
            .eq("month_key", month_key)
            .limit(1)
            .execute()
        )
        data = res.data or []
        return (data[0] if data else None), None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)
