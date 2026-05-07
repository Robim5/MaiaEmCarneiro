""" agendamento com APScheduler """

from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from worker.jobs import run_job
from worker.settings import Settings


def start_scheduler(settings: Settings) -> None:
    scheduler = BlockingScheduler(timezone=settings.timezone)

    for scheduled_time in settings.schedule_times:
        hour, minute = scheduled_time.split(":")
        scheduler.add_job(
            run_job,
            CronTrigger(hour=int(hour), minute=int(minute), timezone=settings.timezone),
            args=[settings],
            id=f"airlabs_rollup_{hour}_{minute}",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=30 * 60,
        )
        logging.info("Job agendado para %s %s", scheduled_time, settings.timezone_name)

    if settings.run_on_start:
        run_job(settings)

    scheduler.start()
