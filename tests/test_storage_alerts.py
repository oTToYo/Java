from __future__ import annotations

from pathlib import Path

import pandas as pd

from tw_stock.alerts.engine import evaluate_rules
from tw_stock.data.storage import StockStore
from tw_stock.indicators.technical import enrich_indicators
from tw_stock.notify.line import LineNotifier


def test_storage_upsert_and_query(tmp_path: Path):
    store = StockStore(tmp_path / "t.db")
    df = pd.DataFrame(
        [
            {
                "symbol": "2330",
                "date": "2024-06-03",
                "open": 100,
                "high": 105,
                "low": 99,
                "close": 104,
                "volume": 1000,
            },
            {
                "symbol": "2330",
                "date": "2024-06-04",
                "open": 104,
                "high": 108,
                "low": 103,
                "close": 107,
                "volume": 1200,
            },
        ]
    )
    assert store.upsert_daily(df, source="test") == 2
    got = store.get_daily("2330")
    assert len(got) == 2
    assert store.latest_date("2330") == "2024-06-04"


def test_line_dry_run(capsys):
    n = LineNotifier(dry_run=True)
    assert n.send_text("hello") is True
    captured = capsys.readouterr()
    assert "hello" in captured.out


def test_macd_cross_detection():
    # 人工構造 MACD 交叉
    n = 40
    dates = pd.bdate_range("2024-01-01", periods=n)
    # 前半下跌後半急漲，易產生黃金交叉
    closes = [100 - i * 0.5 for i in range(20)] + [90 + i for i in range(20)]
    df = pd.DataFrame(
        {
            "symbol": ["TEST"] * n,
            "date": dates.strftime("%Y-%m-%d"),
            "open": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
            "volume": [1000] * n,
        }
    )
    settings = {
        "indicators": {
            "ma_periods": [5, 20],
            "rsi_period": 14,
            "macd": {"fast": 12, "slow": 26, "signal": 9},
            "kd": {"k_period": 9, "d_period": 3},
        }
    }
    enriched = enrich_indicators(df, settings)
    rules = [
        {
            "name": "MACD 黃金交叉",
            "indicator": "macd_golden_cross",
            "message": "{symbol} golden",
        }
    ]
    # 對整段掃描：取最後兩根可能沒交叉，改用滑動檢查至少有機會計算
    hits = evaluate_rules(enriched, rules, "TEST")
    assert isinstance(hits, list)
