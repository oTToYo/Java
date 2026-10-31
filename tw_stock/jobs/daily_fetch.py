"""每日抓取觀察清單歷史／當日行情並寫入資料庫。"""

from __future__ import annotations

import logging
from typing import Any

from tw_stock.data.fetcher import (
    fetch_twse_day_all,
    fetch_watchlist_history,
)
from tw_stock.data.storage import StockStore

logger = logging.getLogger(__name__)


def run_daily_fetch(
    settings: dict[str, Any],
    store: StockStore | None = None,
    symbols: list[str] | None = None,
    include_market_snapshot: bool = True,
) -> dict[str, int]:
    storage_cfg = settings.get("storage") or {}
    store = store or StockStore(storage_cfg.get("db_path", "data/stocks.db"))
    symbols = symbols or list(settings.get("watchlist") or [])

    counts: dict[str, int] = {}
    histories = fetch_watchlist_history(symbols, settings)
    source = (settings.get("fetch") or {}).get("historical_source", "yfinance")
    for symbol, df in histories.items():
        n = store.upsert_daily(df, source=source)
        counts[symbol] = n
        logger.info("%s 寫入 %s 筆", symbol, n)

    if include_market_snapshot:
        fetch_cfg = settings.get("fetch") or {}
        url = fetch_cfg.get(
            "twse_day_all_url",
            "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
        )
        try:
            market = fetch_twse_day_all(url)
            if not market.empty:
                # 只更新觀察清單內的股票，避免一次塞入全市場
                watch = set(symbols)
                subset = market[market["symbol"].isin(watch)]
                if not subset.empty:
                    n = store.upsert_daily(subset, source="twse_day_all")
                    counts["__twse_day_all__"] = n
                    logger.info("TWSE 當日觀察清單更新 %s 筆", n)
        except Exception as exc:  # noqa: BLE001
            logger.warning("TWSE 當日全市場抓取失敗（可於收盤後重試）: %s", exc)

    return counts
