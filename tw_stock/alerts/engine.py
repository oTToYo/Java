"""依技術指標規則產生通知，並可選擇觸發自動下單。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from tw_stock.data.storage import StockStore
from tw_stock.indicators.technical import enrich_indicators
from tw_stock.notify.line import LineNotifier
from tw_stock.trading.sinopac import SinoPacTrader

logger = logging.getLogger(__name__)


@dataclass
class AlertHit:
    symbol: str
    rule_name: str
    message: str
    close: float | None = None


def _crossed_up(prev_a: float, prev_b: float, a: float, b: float) -> bool:
    return prev_a <= prev_b and a > b


def _crossed_down(prev_a: float, prev_b: float, a: float, b: float) -> bool:
    return prev_a >= prev_b and a < b


def evaluate_rules(df: pd.DataFrame, rules: list[dict[str, Any]], symbol: str) -> list[AlertHit]:
    if df is None or len(df) < 2:
        return []

    cur = df.iloc[-1]
    prev = df.iloc[-2]
    hits: list[AlertHit] = []

    for rule in rules:
        name = rule.get("name", "unnamed")
        indicator = rule.get("indicator")
        template = rule.get("message", "{symbol} 觸發 {name}")
        triggered = False
        ctx: dict[str, Any] = {
            "symbol": symbol,
            "name": name,
            "close": float(cur["close"]) if pd.notna(cur.get("close")) else None,
            "value": None,
            "ma": None,
        }

        if indicator == "rsi":
            value = cur.get("rsi")
            if pd.isna(value):
                continue
            ctx["value"] = float(value)
            op = rule.get("op", "<")
            threshold = float(rule.get("value", 30))
            triggered = value < threshold if op == "<" else value > threshold

        elif indicator in {"close_above_ma", "close_below_ma"}:
            ma_p = int(rule.get("ma", 20))
            col = f"ma{ma_p}"
            if col not in cur or pd.isna(cur[col]) or pd.isna(cur["close"]):
                continue
            ctx["ma"] = float(cur[col])
            ctx["value"] = float(cur["close"])
            if indicator == "close_above_ma":
                triggered = float(prev["close"]) <= float(prev[col]) and float(
                    cur["close"]
                ) > float(cur[col])
            else:
                triggered = float(prev["close"]) >= float(prev[col]) and float(
                    cur["close"]
                ) < float(cur[col])

        elif indicator == "macd_golden_cross":
            needed = ["macd", "macd_signal"]
            if any(pd.isna(cur.get(c)) or pd.isna(prev.get(c)) for c in needed):
                continue
            triggered = _crossed_up(
                float(prev["macd"]),
                float(prev["macd_signal"]),
                float(cur["macd"]),
                float(cur["macd_signal"]),
            )
            ctx["value"] = float(cur["macd"])

        elif indicator == "macd_death_cross":
            needed = ["macd", "macd_signal"]
            if any(pd.isna(cur.get(c)) or pd.isna(prev.get(c)) for c in needed):
                continue
            triggered = _crossed_down(
                float(prev["macd"]),
                float(prev["macd_signal"]),
                float(cur["macd"]),
                float(cur["macd_signal"]),
            )
            ctx["value"] = float(cur["macd"])

        elif indicator == "kd_golden_cross":
            if any(pd.isna(cur.get(c)) or pd.isna(prev.get(c)) for c in ("k", "d")):
                continue
            triggered = _crossed_up(
                float(prev["k"]), float(prev["d"]), float(cur["k"]), float(cur["d"])
            )
            ctx["value"] = float(cur["k"])

        elif indicator == "kd_death_cross":
            if any(pd.isna(cur.get(c)) or pd.isna(prev.get(c)) for c in ("k", "d")):
                continue
            triggered = _crossed_down(
                float(prev["k"]), float(prev["d"]), float(cur["k"]), float(cur["d"])
            )
            ctx["value"] = float(cur["k"])

        else:
            logger.warning("未知指標規則: %s", indicator)
            continue

        if triggered:
            try:
                message = template.format(**ctx)
            except Exception:  # noqa: BLE001
                message = f"{symbol} 觸發 {name}"
            hits.append(
                AlertHit(
                    symbol=symbol,
                    rule_name=name,
                    message=message,
                    close=ctx.get("close"),
                )
            )
    return hits


def run_alerts(
    settings: dict[str, Any],
    store: StockStore,
    symbols: list[str] | None = None,
    notifier: LineNotifier | None = None,
    trader: SinoPacTrader | None = None,
) -> list[AlertHit]:
    alert_cfg = settings.get("alerts") or {}
    if not alert_cfg.get("enabled", True):
        logger.info("alerts.enabled=false，略過")
        return []

    rules = alert_cfg.get("rules") or []
    cooldown_hours = int(alert_cfg.get("cooldown_hours", 24))
    since = (datetime.now(timezone.utc) - timedelta(hours=cooldown_hours)).isoformat()

    notifier = notifier or LineNotifier.from_settings(settings)
    trader = trader or SinoPacTrader(settings, store=store)
    auto = (settings.get("sinopac") or {}).get("auto_trade") or {}
    auto_enabled = bool(auto.get("enabled", False))
    buy_on = set(auto.get("buy_on") or [])
    sell_on = set(auto.get("sell_on") or [])
    qty = int(auto.get("quantity", 1))
    price_type = str(auto.get("price_type", "MKT"))

    symbols = symbols or settings.get("watchlist") or store.list_symbols()
    all_hits: list[AlertHit] = []

    for symbol in symbols:
        df = store.get_daily(symbol)
        if df.empty:
            logger.warning("%s 無資料，略過告警", symbol)
            continue
        enriched = enrich_indicators(df, settings)
        hits = evaluate_rules(enriched, rules, symbol)
        for hit in hits:
            if store.recent_alert(symbol, hit.rule_name, since):
                logger.info("冷卻中，略過 %s / %s", symbol, hit.rule_name)
                continue
            ok = notifier.send_text(hit.message)
            if ok:
                store.record_alert(
                    symbol,
                    hit.rule_name,
                    datetime.now(timezone.utc).isoformat(),
                    hit.message,
                )
                all_hits.append(hit)

            if auto_enabled:
                action = None
                if hit.rule_name in buy_on:
                    action = "Buy"
                elif hit.rule_name in sell_on:
                    action = "Sell"
                if action:
                    # 僅在雙重確認後實盤下單；其餘一律 dry-run，避免誤觸發
                    if trader.can_place_real_order():
                        trader.place_stock_order(
                            symbol,
                            action,
                            quantity=qty,
                            price=hit.close,
                            price_type=price_type,
                        )
                    else:
                        trader.dry_run_order(
                            symbol, action, quantity=qty, price=hit.close
                        )

    return all_hits
