"""SQLite 股價儲存。"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from tw_stock.config import resolve_path


SCHEMA = """
CREATE TABLE IF NOT EXISTS daily_prices (
    symbol TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    source TEXT,
    PRIMARY KEY (symbol, date)
);

CREATE TABLE IF NOT EXISTS alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    fired_at TEXT NOT NULL,
    message TEXT,
    UNIQUE (symbol, rule_name, fired_at)
);

CREATE TABLE IF NOT EXISTS order_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    action TEXT NOT NULL,
    quantity INTEGER,
    price REAL,
    status TEXT,
    simulation INTEGER,
    created_at TEXT NOT NULL,
    raw TEXT
);
"""


class StockStore:
    def __init__(self, db_path: str | Path):
        self.db_path = resolve_path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def upsert_daily(self, df: pd.DataFrame, source: str = "unknown") -> int:
        if df.empty:
            return 0
        required = {"symbol", "date", "open", "high", "low", "close", "volume"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"缺少欄位: {missing}")

        rows = []
        for row in df.itertuples(index=False):
            rows.append(
                (
                    str(row.symbol),
                    str(row.date)[:10],
                    float(row.open) if pd.notna(row.open) else None,
                    float(row.high) if pd.notna(row.high) else None,
                    float(row.low) if pd.notna(row.low) else None,
                    float(row.close) if pd.notna(row.close) else None,
                    float(row.volume) if pd.notna(row.volume) else None,
                    source,
                )
            )

        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO daily_prices
                    (symbol, date, open, high, low, close, volume, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, date) DO UPDATE SET
                    open=excluded.open,
                    high=excluded.high,
                    low=excluded.low,
                    close=excluded.close,
                    volume=excluded.volume,
                    source=excluded.source
                """,
                rows,
            )
        return len(rows)

    def get_daily(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        sql = "SELECT * FROM daily_prices WHERE symbol = ?"
        params: list[object] = [symbol]
        if start:
            sql += " AND date >= ?"
            params.append(start)
        if end:
            sql += " AND date <= ?"
            params.append(end)
        sql += " ORDER BY date ASC"
        with self._connect() as conn:
            df = pd.read_sql_query(sql, conn, params=params)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df

    def list_symbols(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT symbol FROM daily_prices ORDER BY symbol"
            ).fetchall()
        return [r["symbol"] for r in rows]

    def latest_date(self, symbol: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT MAX(date) AS d FROM daily_prices WHERE symbol = ?",
                (symbol,),
            ).fetchone()
        return row["d"] if row and row["d"] else None

    def record_alert(self, symbol: str, rule_name: str, fired_at: str, message: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO alert_history
                    (symbol, rule_name, fired_at, message)
                VALUES (?, ?, ?, ?)
                """,
                (symbol, rule_name, fired_at, message),
            )

    def recent_alert(
        self, symbol: str, rule_name: str, since: str
    ) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT 1 FROM alert_history
                WHERE symbol = ? AND rule_name = ? AND fired_at >= ?
                LIMIT 1
                """,
                (symbol, rule_name, since),
            ).fetchone()
        return row is not None

    def log_order(
        self,
        symbol: str,
        action: str,
        quantity: int,
        price: float | None,
        status: str,
        simulation: bool,
        created_at: str,
        raw: str = "",
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO order_log
                    (symbol, action, quantity, price, status, simulation, created_at, raw)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol,
                    action,
                    quantity,
                    price,
                    status,
                    1 if simulation else 0,
                    created_at,
                    raw,
                ),
            )
