"""命令列入口。"""

from __future__ import annotations

import argparse
import logging
import sys

from tw_stock.alerts.engine import run_alerts
from tw_stock.charts.kline import plot_kline
from tw_stock.config import load_settings
from tw_stock.data.storage import StockStore
from tw_stock.indicators.technical import enrich_indicators, latest_snapshot
from tw_stock.jobs.daily_fetch import run_daily_fetch
from tw_stock.jobs.scheduler import start_scheduler
from tw_stock.notify.line import LineNotifier
from tw_stock.trading.sinopac import SinoPacTrader


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def _store(settings) -> StockStore:
    return StockStore((settings.get("storage") or {}).get("db_path", "data/stocks.db"))


def cmd_fetch(args: argparse.Namespace) -> int:
    settings = load_settings()
    symbols = args.symbols.split(",") if args.symbols else None
    counts = run_daily_fetch(
        settings,
        store=_store(settings),
        symbols=symbols,
        include_market_snapshot=not args.skip_market,
    )
    for k, v in counts.items():
        print(f"{k}: {v} rows")
    return 0


def cmd_chart(args: argparse.Namespace) -> int:
    settings = load_settings()
    store = _store(settings)
    symbol = args.symbol
    df = store.get_daily(symbol)
    if df.empty:
        print(f"{symbol} 尚無資料，請先執行 fetch")
        return 1
    chart_dir = (settings.get("storage") or {}).get("chart_dir", "charts")
    path = plot_kline(df, symbol, settings, output_dir=chart_dir)
    print(f"已輸出: {path}")
    return 0


def cmd_indicators(args: argparse.Namespace) -> int:
    settings = load_settings()
    store = _store(settings)
    df = store.get_daily(args.symbol)
    if df.empty:
        print(f"{args.symbol} 尚無資料")
        return 1
    snap = latest_snapshot(enrich_indicators(df, settings))
    keys = [
        "date",
        "close",
        "ma5",
        "ma20",
        "ma60",
        "rsi",
        "macd",
        "macd_signal",
        "k",
        "d",
    ]
    for key in keys:
        if key in snap:
            print(f"{key}: {snap[key]}")
    return 0


def cmd_alert(args: argparse.Namespace) -> int:
    settings = load_settings()
    store = _store(settings)
    symbols = args.symbols.split(",") if args.symbols else None
    hits = run_alerts(settings, store=store, symbols=symbols)
    if not hits:
        print("沒有觸發任何規則")
    else:
        for hit in hits:
            print(f"[ALERT] {hit.message}")
    return 0


def cmd_notify_test(args: argparse.Namespace) -> int:
    settings = load_settings()
    if args.live:
        settings.setdefault("line", {})["dry_run"] = False
    notifier = LineNotifier.from_settings(settings)
    ok = notifier.send_text(args.message or "台股機器人測試訊息")
    return 0 if ok else 1


def cmd_order(args: argparse.Namespace) -> int:
    settings = load_settings()
    store = _store(settings)
    trader = SinoPacTrader(settings, store=store)
    if args.dry_run or not trader.can_place_real_order():
        result = trader.dry_run_order(
            args.symbol, args.action, quantity=args.qty, price=args.price
        )
    else:
        result = trader.place_stock_order(
            args.symbol,
            args.action,
            quantity=args.qty,
            price=args.price,
            price_type=args.price_type,
        )
        trader.logout()
    print(result)
    return 0 if result.ok else 1


def cmd_schedule(_: argparse.Namespace) -> int:
    start_scheduler(load_settings())
    return 0


def cmd_dashboard(_: argparse.Namespace) -> int:
    import subprocess
    from tw_stock.config import project_root

    app = project_root() / "tw_stock" / "dashboard.py"
    return subprocess.call(
        [sys.executable, "-m", "streamlit", "run", str(app), "--server.headless=true"]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tw-stock",
        description="台灣股市：每日抓取 / K線 / 指標通知 / 永豐下單",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p_fetch = sub.add_parser("fetch", help="抓取觀察清單日線並存入 SQLite")
    p_fetch.add_argument("--symbols", help="逗號分隔代號，預設用 settings watchlist")
    p_fetch.add_argument(
        "--skip-market", action="store_true", help="略過證交所當日全市場更新"
    )
    p_fetch.set_defaults(func=cmd_fetch)

    p_chart = sub.add_parser("chart", help="繪製 K 線圖")
    p_chart.add_argument("symbol", help="股票代號，如 2330")
    p_chart.set_defaults(func=cmd_chart)

    p_ind = sub.add_parser("indicators", help="顯示最新技術指標")
    p_ind.add_argument("symbol")
    p_ind.set_defaults(func=cmd_indicators)

    p_alert = sub.add_parser("alert", help="檢查指標規則並推播 LINE")
    p_alert.add_argument("--symbols")
    p_alert.set_defaults(func=cmd_alert)

    p_notify = sub.add_parser("notify-test", help="測試 LINE 推播")
    p_notify.add_argument("--message")
    p_notify.add_argument(
        "--live", action="store_true", help="關閉 dry_run，真實送出"
    )
    p_notify.set_defaults(func=cmd_notify_test)

    p_order = sub.add_parser("order", help="下單（預設 dry-run / 模擬）")
    p_order.add_argument("symbol")
    p_order.add_argument("action", choices=["Buy", "Sell", "buy", "sell"])
    p_order.add_argument("--qty", type=int, default=1)
    p_order.add_argument("--price", type=float)
    p_order.add_argument("--price-type", default="MKT", choices=["MKT", "LMT"])
    p_order.add_argument(
        "--dry-run",
        action="store_true",
        help="只記錄不下單（未開實盤時也會自動 dry-run）",
    )
    p_order.set_defaults(func=cmd_order)

    p_sched = sub.add_parser("schedule", help="啟動每日排程")
    p_sched.set_defaults(func=cmd_schedule)

    p_dash = sub.add_parser("dashboard", help="啟動 Streamlit K 線儀表板")
    p_dash.set_defaults(func=cmd_dashboard)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
