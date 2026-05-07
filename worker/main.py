""" ponto de entrada do worker (Railway ou local) """

from __future__ import annotations

import argparse
import logging
import sys

from worker.db import delete_all_rollups, get_client
from worker.jobs import run_job
from worker.scheduler import start_scheduler
from worker.settings import load_settings, load_supabase_credentials, setup_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="Worker Airlabs OPO para Supabase")
    parser.add_argument("--once", action="store_true", help="Executa o job uma vez e termina")
    parser.add_argument(
        "--reset-table",
        action="store_true",
        help="Apaga todas as linhas de flight_monthly_rollup (precisa de --yes)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirma operações destrutivas (--reset-table)",
    )
    args = parser.parse_args()

    setup_logging()

    if args.reset_table:
        if not args.yes:
            logging.error("Para apagar todos os registos, corre de novo com --yes")
            sys.exit(1)
        url, key = load_supabase_credentials()
        delete_all_rollups(get_client(url, key))
        logging.info("Reset concluído. Podes correr --once para popular o dia atual.")
        return

    settings = load_settings()

    if args.once:
        run_job(settings)
        return

    start_scheduler(settings)


if __name__ == "__main__":
    main()
