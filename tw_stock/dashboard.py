"""Streamlit K 線與指標儀表板。"""

from __future__ import annotations

import sys
from pathlib import Path

# 允許直接 streamlit run 本檔
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from tw_stock.charts.kline import plot_kline
from tw_stock.config import load_settings
from tw_stock.data.storage import StockStore
from tw_stock.indicators.technical import enrich_indicators, latest_snapshot
from tw_stock.jobs.daily_fetch import run_daily_fetch


st.set_page_config(page_title="台股 K 線機器人", layout="wide")
st.title("台股 K 線與指標")
st.caption("每日抓取 · 技術指標 · LINE 通知 · 永豐 Shioaji 下單")

settings = load_settings()
store = StockStore((settings.get("storage") or {}).get("db_path", "data/stocks.db"))

watch = settings.get("watchlist") or []
db_symbols = store.list_symbols()
options = sorted(set(watch) | set(db_symbols)) or ["2330"]

col_a, col_b, col_c = st.columns([2, 1, 1])
with col_a:
    symbol = st.selectbox("股票代號", options=options, index=0)
with col_b:
    if st.button("抓取／更新資料", use_container_width=True):
        with st.spinner("下載中…"):
            counts = run_daily_fetch(settings, store=store, symbols=[symbol])
        st.success(f"完成：{counts}")
with col_c:
    refresh = st.button("重新整理圖表", use_container_width=True)

df = store.get_daily(symbol)
if df.empty:
    st.warning("尚無資料，請先按「抓取／更新資料」或執行 `python -m tw_stock.cli fetch`")
    st.stop()

enriched = enrich_indicators(df, settings)
snap = latest_snapshot(enriched)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("收盤", f"{snap.get('close', float('nan')):.2f}")
m2.metric("RSI", f"{snap.get('rsi', float('nan')):.1f}" if snap.get("rsi") is not None else "-")
m3.metric("MA20", f"{snap.get('ma20', float('nan')):.2f}" if snap.get("ma20") is not None else "-")
m4.metric("MACD", f"{snap.get('macd', float('nan')):.3f}" if snap.get("macd") is not None else "-")
m5.metric("KD", f"{snap.get('k', float('nan')):.1f}/{snap.get('d', float('nan')):.1f}" if snap.get("k") is not None else "-")

chart_dir = (settings.get("storage") or {}).get("chart_dir", "charts")
try:
    path = plot_kline(df, symbol, settings, output_dir=chart_dir)
    st.image(str(path), caption=f"{symbol} K 線", use_container_width=True)
except Exception as exc:  # noqa: BLE001
    st.error(f"繪圖失敗: {exc}")

st.subheader("最近日線")
show = enriched.tail(30).copy()
show["date"] = pd.to_datetime(show["date"]).dt.strftime("%Y-%m-%d")
cols = [
    c
    for c in [
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "ma5",
        "ma20",
        "ma60",
        "rsi",
        "macd",
        "k",
        "d",
    ]
    if c in show.columns
]
st.dataframe(show[cols], use_container_width=True, hide_index=True)

st.subheader("告警規則")
st.json((settings.get("alerts") or {}).get("rules") or [])

if refresh:
    st.rerun()
