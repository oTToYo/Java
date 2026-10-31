"""台股日線資料抓取：證交所當日全市場 + yfinance / FinMind 歷史回補。"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import requests

logger = logging.getLogger(__name__)


def _normalize_ohlcv(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    cols = {c.lower(): c for c in df.columns}
    mapping = {}
    for key in ("open", "high", "low", "close", "volume"):
        if key in cols:
            mapping[cols[key]] = key
        elif key.title() in df.columns:
            mapping[key.title()] = key
        elif key.capitalize() in df.columns:
            mapping[key.capitalize()] = key

    out = df.rename(columns=mapping).copy()
    if "date" not in out.columns:
        if isinstance(out.index, pd.DatetimeIndex):
            out = out.reset_index()
            date_col = out.columns[0]
            out = out.rename(columns={date_col: "date"})
        else:
            raise ValueError("找不到 date 欄位")

    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out["symbol"] = symbol
    for col in ("open", "high", "low", "close", "volume"):
        if col not in out.columns:
            out[col] = None
        out[col] = pd.to_numeric(out[col], errors="coerce")

    out = out[["symbol", "date", "open", "high", "low", "close", "volume"]]
    out = out.dropna(subset=["close"])
    out = out[out["close"] > 0]
    return out.reset_index(drop=True)


def yahoo_symbol(symbol: str, listed: bool = True) -> str:
    code = symbol.strip().upper()
    if code.endswith(".TW") or code.endswith(".TWO"):
        return code
    return f"{code}.TW" if listed else f"{code}.TWO"


def fetch_yfinance_history(
    symbol: str,
    start: str | None = None,
    end: str | None = None,
    lookback_days: int = 365,
) -> pd.DataFrame:
    import yfinance as yf

    if not start:
        start = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    end = end or datetime.now().strftime("%Y-%m-%d")

    frames: list[pd.DataFrame] = []
    for listed in (True, False):
        ticker = yahoo_symbol(symbol, listed=listed)
        try:
            raw = yf.download(
                ticker,
                start=start,
                end=end,
                auto_adjust=False,
                progress=False,
                threads=False,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("yfinance 下載失敗 %s: %s", ticker, exc)
            continue
        if raw is None or raw.empty:
            continue
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = [c[0] for c in raw.columns]
        frames.append(_normalize_ohlcv(raw, symbol))
        break

    if not frames:
        logger.warning("找不到 %s 的 yfinance 資料", symbol)
        return pd.DataFrame(
            columns=["symbol", "date", "open", "high", "low", "close", "volume"]
        )
    return frames[0]


def fetch_finmind_history(
    symbol: str,
    start: str | None = None,
    end: str | None = None,
    token: str = "",
    lookback_days: int = 365,
) -> pd.DataFrame:
    from FinMind.data import DataLoader

    if not start:
        start = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    end = end or datetime.now().strftime("%Y-%m-%d")

    api = DataLoader()
    if token:
        api.login_by_token(api_token=token)
    df = api.taiwan_stock_daily(stock_id=symbol, start_date=start, end_date=end)
    if df is None or df.empty:
        return pd.DataFrame(
            columns=["symbol", "date", "open", "high", "low", "close", "volume"]
        )

    renamed = df.rename(
        columns={
            "stock_id": "symbol",
            "max": "high",
            "min": "low",
            "Trading_Volume": "volume",
        }
    )
    return _normalize_ohlcv(renamed, symbol)


def _parse_twse_number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).replace(",", "").replace("--", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def fetch_twse_day_all(url: str) -> pd.DataFrame:
    """證交所當日全市場收盤行情。"""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    if not payload:
        return pd.DataFrame(
            columns=["symbol", "date", "open", "high", "low", "close", "volume"]
        )

    today = datetime.now().strftime("%Y-%m-%d")
    rows = []
    for item in payload:
        symbol = str(item.get("Code") or item.get("證券代號") or "").strip()
        if not symbol:
            continue
        close = _parse_twse_number(item.get("ClosingPrice") or item.get("收盤價"))
        if close is None or close <= 0:
            continue
        rows.append(
            {
                "symbol": symbol,
                "date": today,
                "open": _parse_twse_number(item.get("OpeningPrice") or item.get("開盤價")),
                "high": _parse_twse_number(item.get("HighestPrice") or item.get("最高價")),
                "low": _parse_twse_number(item.get("LowestPrice") or item.get("最低價")),
                "close": close,
                "volume": _parse_twse_number(
                    item.get("TradeVolume") or item.get("成交股數")
                ),
            }
        )
    return pd.DataFrame(rows)


def fetch_watchlist_history(
    symbols: list[str],
    settings: dict[str, Any],
    start: str | None = None,
) -> dict[str, pd.DataFrame]:
    fetch_cfg = settings.get("fetch", {})
    source = fetch_cfg.get("historical_source", "yfinance")
    lookback = int(fetch_cfg.get("lookback_days", 365))
    token = (settings.get("finmind") or {}).get("token", "")

    result: dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        logger.info("抓取歷史日線 %s via %s", symbol, source)
        if source == "finmind":
            df = fetch_finmind_history(
                symbol, start=start, token=token, lookback_days=lookback
            )
        else:
            df = fetch_yfinance_history(symbol, start=start, lookback_days=lookback)
        result[symbol] = df
    return result
