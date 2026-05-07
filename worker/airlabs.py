""" cliente HTTP para schedules airlabs """

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import requests

from worker.constants import AIRLABS_SCHEDULES_URL
from worker.settings import Settings


def extract_airlabs_records(payload: Any) -> tuple[list[dict[str, Any]], bool]:
    """Extrai lista de voos e flag has_more da resposta Airlabs."""
    if isinstance(payload, list):
        return payload, False

    if not isinstance(payload, dict):
        raise RuntimeError("Resposta inesperada do Airlabs")

    if payload.get("error"):
        raise RuntimeError(f"Erro da Airlabs: {payload['error']}")

    records = payload.get("response", [])
    if not isinstance(records, list):
        raise RuntimeError("Campo response do Airlabs não é uma lista")

    request_meta = payload.get("request") or {}
    has_more = bool(request_meta.get("has_more")) if isinstance(request_meta, dict) else False
    return records, has_more


def fetch_airlabs_schedules(settings: Settings, direction: str) -> list[dict[str, Any]]:
    if direction not in {"dep", "arr"}:
        raise ValueError("direction deve ser 'dep' ou 'arr'")

    airport_param = "dep_iata" if direction == "dep" else "arr_iata"
    offset = 0
    all_records: list[dict[str, Any]] = []

    while True:
        params = {
            "api_key": settings.airlabs_api_key,
            airport_param: settings.airport_iata,
            "limit": settings.airlabs_limit,
            "offset": offset,
            "_fields": "flight_iata,flight_icao,flight_number,dep_iata,arr_iata,dep_time,arr_time,status",
        }

        response = requests.get(AIRLABS_SCHEDULES_URL, params=params, timeout=30)
        response.raise_for_status()

        records, has_more = extract_airlabs_records(response.json())
        all_records.extend(records)

        if not has_more or len(records) == 0:
            break

        offset += settings.airlabs_limit

    logging.info("Airlabs %s: recebidos %s registos", direction, len(all_records))
    return all_records


def is_record_for_day(record: dict[str, Any], direction: str, target_day: date) -> bool:
    time_field = "dep_time" if direction == "dep" else "arr_time"
    raw_time = record.get(time_field)

    if not isinstance(raw_time, str) or len(raw_time) < 10:
        return False

    return raw_time[:10] == target_day.isoformat()


def count_daily_airport_movements(settings: Settings, target_day: date) -> int:
    departures = fetch_airlabs_schedules(settings, "dep")
    arrivals = fetch_airlabs_schedules(settings, "arr")

    today_departures = [item for item in departures if is_record_for_day(item, "dep", target_day)]
    today_arrivals = [item for item in arrivals if is_record_for_day(item, "arr", target_day)]

    total = len(today_departures) + len(today_arrivals)
    logging.info(
        "Total %s para %s: %s partidas + %s chegadas = %s voos",
        settings.airport_iata,
        target_day.isoformat(),
        len(today_departures),
        len(today_arrivals),
        total,
    )
    return total
