"""APScheduler 排程：每日抓資料 + 檢查指標通知。"""

from __future__ import annotations

import logging
from typing import Any

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

from tw_stock.alerts.engine import run_alerts
from tw_stock.config import load_settings
from tw_stock.data.storage import StockStore
from tw_stock.jobs.daily_fetch import run_daily_fetch

logger = logging.getLogger(__name__)


def _parse_cron(expr: str) -> dict[str, str]:
    """簡易 5 欄 cron：分 時 日 月 週。"""
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError(f"無效 cron: {expr}")
    minute, hour, day, month, day_of_week = parts
    return {
        "minute": minute,
        "hour": hour,
        "day": day,
        "month": month,
        "day_of_week": day_of_week,
    }


def start_scheduler(settings: dict[str, Any] | None = None) -> None:
    settings = settings or load_settings()
    sched_cfg = settings.get("scheduler") or {}
    tz_name = sched_cfg.get("timezone", "Asia/Taipei")
    tz = ZoneInfo(tz_name)
    store = StockStore((settings.get("storage") or {}).get("db_path", "data/stocks.db"))

    scheduler = BlockingScheduler(timezone=tz)

    fetch_cron = _parse_cron(sched_cfg.get("daily_fetch_cron", "30 16 * * 1-5"))
    alert_cron = _parse_cron(sched_cfg.get("alert_cron", "0 17 * * 1-5"))

    def job_fetch() -> None:
        logger.info("排程：開始每日抓取")
        run_daily_fetch(settings, store=store)

    def job_alert() -> None:
        logger.info("排程：開始檢查指標通知")
        run_alerts(settings, store=store)

    scheduler.add_job(
        job_fetch,
        CronTrigger(timezone=tz, **fetch_cron),
        id="daily_fetch",
        replace_existing=True,
    )
    scheduler.add_job(
        job_alert,
        CronTrigger(timezone=tz, **alert_cron),
        id="alerts",
        replace_existing=True,
    )

    logger.info(
        "排程已啟動 timezone=%s fetch=%s alert=%s",
        tz_name,
        sched_cfg.get("daily_fetch_cron"),
        sched_cfg.get("alert_cron"),
    )
    scheduler.start()
