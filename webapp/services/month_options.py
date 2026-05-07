""" lista de meses até ao atual (para dropdown sem futuros) """

from __future__ import annotations

from datetime import date


def month_keys_backwards(today: date, max_months: int = 48) -> list[str]:
    """ do mais antigo ao mais recente, sempre <= mês atual """
    y, m = today.year, today.month
    keys: list[str] = []
    for _ in range(max_months):
        keys.append(f"{y}-{m:02d}")
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return list(reversed(keys))
