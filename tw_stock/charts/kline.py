"""K 線圖繪製（mplfinance）。"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import mplfinance as mpf
import pandas as pd

from tw_stock.config import resolve_path
from tw_stock.indicators.technical import enrich_indicators


def _to_ohlc(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"])
    out = out.set_index("date")
    out = out.rename(
        columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )
    return out[["Open", "High", "Low", "Close", "Volume"]].dropna(how="any")


def plot_kline(
    df: pd.DataFrame,
    symbol: str,
    settings: dict,
    output_dir: str | Path = "charts",
    show_volume: bool = True,
) -> Path:
    if df.empty:
        raise ValueError(f"{symbol} 沒有可繪製的資料")

    enriched = enrich_indicators(df, settings)
    ohlc = _to_ohlc(enriched)
    if ohlc.empty:
        raise ValueError(f"{symbol} OHLC 資料不足")

    addplots = []
    style = mpf.make_mpf_style(
        base_mpf_style="yahoo",
        marketcolors=mpf.make_marketcolors(
            up="#c0392b",
            down="#27ae60",
            edge="inherit",
            wick="inherit",
            volume="in",
        ),
        gridstyle=":",
        y_on_right=True,
    )

    ma_periods = settings.get("indicators", {}).get("ma_periods", [5, 20, 60])
    colors = ["#2980b9", "#8e44ad", "#d35400", "#16a085"]
    for i, p in enumerate(ma_periods):
        col = f"ma{p}"
        if col in enriched.columns:
            series = enriched.set_index(pd.to_datetime(enriched["date"]))[col]
            series = series.reindex(ohlc.index)
            addplots.append(
                mpf.make_addplot(series, color=colors[i % len(colors)], width=1.0)
            )

    out_dir = resolve_path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{symbol}_kline.png"

    has_rsi = "rsi" in enriched.columns and enriched["rsi"].notna().any()
    if has_rsi:
        rsi = enriched.set_index(pd.to_datetime(enriched["date"]))["rsi"].reindex(
            ohlc.index
        )
        rsi_panel = 2 if show_volume else 1
        addplots.append(
            mpf.make_addplot(rsi, panel=rsi_panel, color="#e67e22", ylabel="RSI")
        )

    # panel_ratios 為 list/tuple：主圖、成交量、（可選）RSI
    if show_volume and has_rsi:
        ratios: tuple[float, ...] = (3, 1, 1)
    elif show_volume:
        ratios = (3, 1)
    elif has_rsi:
        ratios = (3, 1)
    else:
        ratios = (1,)

    kwargs = dict(
        type="candle",
        style=style,
        title=f"{symbol} K-Line",
        ylabel="Price",
        volume=show_volume,
        addplot=addplots if addplots else None,
        savefig=dict(fname=str(out_path), dpi=140, bbox_inches="tight"),
        panel_ratios=ratios,
    )
    mpf.plot(ohlc, **kwargs)
    return out_path
