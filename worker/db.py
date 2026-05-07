""" operações Supabase na tabela flight_monthly_rollup """

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any

from dateutil.relativedelta import relativedelta
from supabase import Client, create_client

from worker.constants import TABLE_NAME


def get_client(url: str, key: str) -> Client:
    return create_client(url, key)


def apply_filters(query: Any, filters: dict[str, Any]) -> Any:
    for column, value in filters.items():
        if value is None:
            query = query.is_(column, "null")
        else:
            query = query.eq(column, value)
    return query


def update_or_insert(
    supabase: Client,
    filters: dict[str, Any],
    update_payload: dict[str, Any],
    insert_payload: dict[str, Any],
) -> None:
    """
    Upsert lógico: update com filtros; se não atualizar nenhuma linha, insert.
    Evita depender de on_conflict com índices únicos parciais no PostgREST.
    """
    update_query = supabase.table(TABLE_NAME).update(update_payload)
    update_response = apply_filters(update_query, filters).execute()

    if update_response.data:
        return

    try:
        supabase.table(TABLE_NAME).insert(insert_payload).execute()
    except Exception:
        retry_query = supabase.table(TABLE_NAME).update(update_payload)
        retry_response = apply_filters(retry_query, filters).execute()
        if not retry_response.data:
            raise


def upsert_daily_rollup(supabase: Client, target_day: date, flights: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    month_key = target_day.strftime("%Y-%m")

    filters = {
        "entry_type": "day",
        "day_date": target_day.isoformat(),
    }
    update_payload = {
        "flights": flights,
        "month_key": month_key,
        "source": "airlabs",
        "updated_at": now,
    }
    insert_payload = {
        "entry_type": "day",
        "day_date": target_day.isoformat(),
        "month_key": month_key,
        "flights": flights,
        "source": "airlabs",
        "updated_at": now,
    }

    update_or_insert(supabase, filters, update_payload, insert_payload)
    logging.info("Rollup diário atualizado: %s = %s", target_day.isoformat(), flights)


def recalculate_month_total(supabase: Client, month_key: str) -> int:
    response = (
        supabase.table(TABLE_NAME)
        .select("flights")
        .eq("entry_type", "day")
        .eq("month_key", month_key)
        .execute()
    )
    return sum(int(row.get("flights") or 0) for row in response.data or [])


def upsert_monthly_rollup(supabase: Client, month_key: str, flights: int) -> None:
    now = datetime.now(timezone.utc).isoformat()

    filters = {
        "entry_type": "month",
        "month_key": month_key,
    }
    update_payload = {
        "flights": flights,
        "source": "airlabs",
        "updated_at": now,
    }
    insert_payload = {
        "entry_type": "month",
        "day_date": None,
        "month_key": month_key,
        "flights": flights,
        "source": "airlabs",
        "updated_at": now,
    }

    update_or_insert(supabase, filters, update_payload, insert_payload)
    logging.info("Rollup mensal atualizado: %s = %s", month_key, flights)


def cleanup_old_rows(supabase: Client, today: date) -> None:
    cutoff_day = today - relativedelta(months=2)
    cutoff_month = cutoff_day.strftime("%Y-%m")

    supabase.table(TABLE_NAME).delete().eq("entry_type", "day").lt(
        "day_date", cutoff_day.isoformat()
    ).execute()

    supabase.table(TABLE_NAME).delete().eq("entry_type", "month").lt(
        "month_key", cutoff_month
    ).execute()

    logging.info(
        "Limpeza concluída: dias antes de %s e meses antes de %s apagados",
        cutoff_day.isoformat(),
        cutoff_month,
    )


def delete_all_rollups(supabase: Client) -> None:
    """Apaga todas as linhas da tabela (reset manual)."""
    # PostgREST exige um filtro no delete; id >= 1 cobre linhas normais com identity.
    supabase.table(TABLE_NAME).delete().gte("id", 1).execute()
    logging.warning("Tabela %s foi esvaziada (reset).", TABLE_NAME)
