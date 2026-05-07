""" pagina principal onde tem vista mensal """

from __future__ import annotations

from flask import Blueprint, render_template, request
from supabase import create_client

from webapp.config import supabase_credentials, today_in_app_tz
from webapp.routes.repo_assets import logo_url
from webapp.services.month_options import month_keys_backwards
from webapp.services.month_view import (
    build_day_cells,
    human_month_label,
    month_nav_keys,
    parse_month_key,
    sum_daily_flights,
)
from webapp.services.repository import fetch_day_rows_for_month, fetch_month_rollup_row

bp = Blueprint("dashboard", __name__)


@bp.get("/")
def index():
    today = today_in_app_tz()

    month_key, parse_warnings = parse_month_key(request.args.get("m"), today)
    prev_m, next_m = month_nav_keys(month_key, today)

    day_rows: list = []
    month_row = None
    fetch_error: str | None = None

    try:
        url, key = supabase_credentials()
        sb = create_client(url, key)

        day_rows, err_days = fetch_day_rows_for_month(sb, month_key)
        if err_days:
            fetch_error = err_days
        else:
            month_row, err_month = fetch_month_rollup_row(sb, month_key)
            if err_month:
                fetch_error = err_month
    except Exception as exc:  # noqa: BLE001
        fetch_error = str(exc)

    cells = build_day_cells(month_key, today, day_rows)
    sum_days = sum_daily_flights(cells)
    has_any_day_data = any(c.has_db_row for c in cells)
    logo = logo_url()
    month_choices = month_keys_backwards(today)
    oldest_m = month_choices[0] if month_choices else month_key
    prev_link = None if month_key == oldest_m else prev_m

    month_total_stored: int | None = None
    if month_row and month_row.get("flights") is not None:
        try:
            month_total_stored = int(month_row["flights"])
        except (TypeError, ValueError):
            month_total_stored = None

    mismatch = (
        month_total_stored is not None
        and has_any_day_data
        and month_total_stored != sum_days
    )

    return render_template(
        "dashboard.html",
        month_key=month_key,
        month_label=human_month_label(month_key),
        prev_m=prev_link,
        next_m=next_m,
        month_choices=month_choices,
        cells=cells,
        month_row=month_row,
        sum_days=sum_days,
        month_total_stored=month_total_stored,
        mismatch=mismatch,
        fetch_error=fetch_error,
        parse_warnings=parse_warnings,
        has_any_day_data=has_any_day_data,
        logo_url=logo,
    )
