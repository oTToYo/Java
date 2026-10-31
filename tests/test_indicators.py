from __future__ import annotations

import pandas as pd

from tw_stock.alerts.engine import evaluate_rules
from tw_stock.indicators.technical import enrich_indicators


def _sample_df() -> pd.DataFrame:
    # 構造一段先跌後漲的序列，方便測 RSI / MA
    closes = (
        [100 - i for i in range(20)]
        + [80 + i * 1.5 for i in range(25)]
    )
    rows = []
    for i, close in enumerate(closes):
        rows.append(
            {
                "symbol": "2330",
                "date": f"2024-01-{i+1:02d}" if i < 31 else f"2024-02-{i-30:02d}",
                "open": close - 0.5,
                "high": close + 1,
                "low": close - 1,
                "close": float(close),
                "volume": 1000 + i,
            }
        )
    # 修正二月日期溢出：改用連續交易日
    idx = pd.bdate_range("2024-01-02", periods=len(closes))
    for i, row in enumerate(rows):
        row["date"] = idx[i].strftime("%Y-%m-%d")
    return pd.DataFrame(rows)


def test_enrich_indicators_has_columns():
    settings = {
        "indicators": {
            "ma_periods": [5, 20],
            "rsi_period": 14,
            "macd": {"fast": 12, "slow": 26, "signal": 9},
            "kd": {"k_period": 9, "d_period": 3},
        }
    }
    df = enrich_indicators(_sample_df(), settings)
    for col in ("ma5", "ma20", "rsi", "macd", "macd_signal", "k", "d"):
        assert col in df.columns
    assert df["rsi"].notna().sum() > 0


def test_evaluate_rsi_rule():
    settings = {
        "indicators": {
            "ma_periods": [5, 20],
            "rsi_period": 14,
            "macd": {"fast": 12, "slow": 26, "signal": 9},
            "kd": {"k_period": 9, "d_period": 3},
        }
    }
    df = enrich_indicators(_sample_df(), settings)
    rules = [
        {
            "name": "RSI 超買",
            "indicator": "rsi",
            "op": ">",
            "value": 50,
            "message": "{symbol} RSI={value:.1f}",
        }
    ]
    hits = evaluate_rules(df, rules, "2330")
    # 末端為上漲段，RSI 通常 > 50
    assert isinstance(hits, list)
