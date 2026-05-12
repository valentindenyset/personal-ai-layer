"""APScheduler-based sync daemon."""
from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from config.settings import settings
from .jobs.incremental_sync import run_incremental_sync

logger = logging.getLogger(__name__)


def start():
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_incremental_sync,
        "interval",
        hours=settings.sync_interval_hours,
        id="incremental_sync",
        max_instances=1,
    )
    logger.info("sync scheduler started — interval: %dh", settings.sync_interval_hours)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start()
