""" montagem da vista mensal (calendário + dados da BD) """

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date
from typing import Any

_MONTH_KEY = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@dataclass(frozen=True)
class DayCell:
    day: date
    weekday_short: str
    flights: int | None
    updated_at: str | None
    source: str | None
    has_db_row: bool


def parse_month_key(raw: str | None, today: date) -> tuple[str, list[str]]:
    """ devolve (month_key, avisos) sempre válido e nunca futuro relativamente a today """
    warnings: list[str] = []
    if not raw or not raw.strip():
        return today.strftime("%Y-%m"), warnings

    candidate = raw.strip()
    if not _MONTH_KEY.match(candidate):
        warnings.append("Parâmetro m inválido, vou a mostrar o mês atual.")
        return today.strftime("%Y-%m"), warnings

    year_s, month_s = candidate.split("-", 1)
    y, m = int(year_s), int(month_s)
    first = date(y, m, 1)
    today_first = date(today.year, today.month, 1)
    if first > today_first:
        warnings.append("Mês futuro não disponível, só limitado ao mês atual.")
        return today.strftime("%Y-%m"), warnings

    return candidate, warnings


def month_nav_keys(month_key: str, today: date) -> tuple[str | None, str | None]:
    """ devolve (prev_key, next_key) ou None se não existir navegação """
    y, m = map(int, month_key.split("-", 1))
    if m == 1:
        prev_key = f"{y - 1}-12"
    else:
        prev_key = f"{y}-{m - 1:02d}"

    if m == 12:
        next_y, next_m = y + 1, 1
    else:
        next_y, next_m = y, m + 1

    next_first = date(next_y, next_m, 1)
    today_first = date(today.year, today.month, 1)
    next_key = f"{next_y}-{next_m:02d}" if next_first <= today_first else None

    return prev_key, next_key


def _weekday_short_pt(d: date) -> str:
    return ("seg", "ter", "qua", "qui", "sex", "sáb", "dom")[d.weekday()]


def build_day_cells(month_key: str, today: date, day_rows: list[dict[str, Any]]) -> list[DayCell]:
    """ uma linha por dia do mês até ao último dia com dados possíveis, corta dias futuros no mês corrente """
    y, m = map(int, month_key.split("-", 1))
    _, last_day = calendar.monthrange(y, m)
    by_day: dict[str, dict[str, Any]] = {}
    for row in day_rows:
        dd = row.get("day_date")
        if isinstance(dd, str) and len(dd) >= 10:
            by_day[dd[:10]] = row

    cells: list[DayCell] = []
    for dom in range(1, last_day + 1):
        d = date(y, m, dom)
        if d > today:
            break
        key = d.isoformat()
        row = by_day.get(key)
        if row is not None:
            flights = row.get("flights")
            try:
                flights_int = int(flights) if flights is not None else None
            except (TypeError, ValueError):
                flights_int = None
            cells.append(
                DayCell(
                    day=d,
                    weekday_short=_weekday_short_pt(d),
                    flights=flights_int,
                    updated_at=row.get("updated_at"),
                    source=row.get("source"),
                    has_db_row=True,
                )
            )
        else:
            cells.append(
                DayCell(
                    day=d,
                    weekday_short=_weekday_short_pt(d),
                    flights=None,
                    updated_at=None,
                    source=None,
                    has_db_row=False,
                )
            )
    return cells


def sum_daily_flights(cells: list[DayCell]) -> int:
    return sum(c.flights or 0 for c in cells if c.has_db_row and c.flights is not None)


_MONTHS_PT = (
    "",
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)


def human_month_label(month_key: str) -> str:
    y, m = map(int, month_key.split("-", 1))
    return f"{_MONTHS_PT[m]} {y}"
