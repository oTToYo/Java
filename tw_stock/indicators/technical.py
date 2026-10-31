"""技術指標：MA / RSI / MACD / KD。"""

from __future__ import annotations

from typing import Any

import pandas as pd


def add_moving_averages(df: pd.DataFrame, periods: list[int]) -> pd.DataFrame:
    out = df.copy()
    for p in periods:
        out[f"ma{p}"] = out["close"].rolling(window=p, min_periods=p).mean()
    return out


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    out = df.copy()
    delta = out["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    out["rsi"] = 100 - (100 / (1 + rs))
    return out


def add_macd(
    df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
) -> pd.DataFrame:
    out = df.copy()
    ema_fast = out["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = out["close"].ewm(span=slow, adjust=False).mean()
    out["macd"] = ema_fast - ema_slow
    out["macd_signal"] = out["macd"].ewm(span=signal, adjust=False).mean()
    out["macd_hist"] = out["macd"] - out["macd_signal"]
    return out


def add_kd(df: pd.DataFrame, k_period: int = 9, d_period: int = 3) -> pd.DataFrame:
    out = df.copy()
    low_min = out["low"].rolling(window=k_period, min_periods=k_period).min()
    high_max = out["high"].rolling(window=k_period, min_periods=k_period).max()
    rsv = (out["close"] - low_min) / (high_max - low_min).replace(0, pd.NA) * 100
    out["k"] = rsv.ewm(alpha=1 / d_period, adjust=False).mean()
    out["d"] = out["k"].ewm(alpha=1 / d_period, adjust=False).mean()
    return out


def enrich_indicators(df: pd.DataFrame, settings: dict[str, Any]) -> pd.DataFrame:
    if df.empty:
        return df
    ind = settings.get("indicators", {})
    out = df.sort_values("date").reset_index(drop=True)
    out = add_moving_averages(out, ind.get("ma_periods", [5, 20, 60]))
    out = add_rsi(out, ind.get("rsi_period", 14))
    macd = ind.get("macd", {})
    out = add_macd(
        out,
        fast=macd.get("fast", 12),
        slow=macd.get("slow", 26),
        signal=macd.get("signal", 9),
    )
    kd = ind.get("kd", {})
    out = add_kd(out, k_period=kd.get("k_period", 9), d_period=kd.get("d_period", 3))
    return out


def latest_snapshot(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {}
    row = df.iloc[-1]
    return {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
