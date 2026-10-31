"""永豐金 Shioaji 下單封裝（預設模擬，實盤需雙重確認）。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from tw_stock.data.storage import StockStore

logger = logging.getLogger(__name__)


@dataclass
class OrderResult:
    ok: bool
    status: str
    raw: str = ""
    price: float | None = None


class SinoPacTrader:
    def __init__(self, settings: dict[str, Any], store: StockStore | None = None):
        self.settings = settings.get("sinopac") or {}
        self.store = store
        self.api = None
        self._logged_in = False

    @property
    def simulation(self) -> bool:
        return bool(self.settings.get("simulation", True))

    @property
    def live_enabled(self) -> bool:
        return bool(self.settings.get("enable_live_trading", False))

    def can_place_real_order(self) -> bool:
        return (not self.simulation) and self.live_enabled

    def login(self) -> None:
        if self._logged_in:
            return

        api_key = self.settings.get("api_key") or ""
        secret = self.settings.get("secret_key") or ""
        if not api_key or not secret:
            raise RuntimeError(
                "缺少 SHIOAJI_API_KEY / SHIOAJI_SECRET_KEY，請先在 .env 設定"
            )

        import shioaji as sj

        # simulation=True 為模擬；實盤需明確關閉模擬並開啟 enable_live_trading
        use_sim = self.simulation or not self.live_enabled
        if not use_sim and not self.live_enabled:
            use_sim = True

        logger.info("登入 Shioaji simulation=%s", use_sim)
        self.api = sj.Shioaji(simulation=use_sim)
        self.api.login(api_key=api_key, secret_key=secret)

        if not use_sim:
            ca_path = self.settings.get("ca_path") or "certs/Sinopac.pfx"
            ca_passwd = self.settings.get("ca_passwd") or ""
            person_id = self.settings.get("person_id") or ""
            if not (ca_path and ca_passwd and person_id):
                raise RuntimeError("實盤下單需要 CA 憑證路徑、密碼與身分證字號")
            self.api.activate_ca(
                ca_path=ca_path,
                ca_passwd=ca_passwd,
                person_id=person_id,
            )
        self._logged_in = True

    def logout(self) -> None:
        if self.api is not None:
            try:
                self.api.logout()
            except Exception as exc:  # noqa: BLE001
                logger.warning("logout 失敗: %s", exc)
        self.api = None
        self._logged_in = False

    def place_stock_order(
        self,
        symbol: str,
        action: str,
        quantity: int = 1,
        price: float | None = None,
        price_type: str = "MKT",
    ) -> OrderResult:
        """action: Buy | Sell"""
        action = action.capitalize()
        if action not in {"Buy", "Sell"}:
            raise ValueError("action 必須是 Buy 或 Sell")

        use_sim = self.simulation or not self.live_enabled
        if not use_sim and not self.can_place_real_order():
            msg = "拒絕實盤下單：請同時設 SHIOAJI_SIMULATION=false 與 ENABLE_LIVE_TRADING=true"
            logger.error(msg)
            return OrderResult(ok=False, status="blocked", raw=msg)

        self.login()
        assert self.api is not None
        import shioaji as sj

        contract = self.api.Contracts.Stocks[symbol]
        if contract is None:
            # 嘗試上市 / 上櫃命名空間
            contract = getattr(self.api.Contracts.Stocks, "TSE", {}).get(symbol) if hasattr(
                self.api.Contracts.Stocks, "TSE"
            ) else None
            if contract is None and hasattr(self.api.Contracts.Stocks, "OTC"):
                contract = self.api.Contracts.Stocks.OTC[symbol]

        if contract is None:
            return OrderResult(ok=False, status="no_contract", raw=f"找不到商品 {symbol}")

        sj_action = sj.constant.Action.Buy if action == "Buy" else sj.constant.Action.Sell

        order_kwargs: dict[str, Any] = {
            "action": sj_action,
            "price": float(price or 0),
            "quantity": int(quantity),
            "order_type": sj.constant.OrderType.ROD,
        }

        # 相容不同版本常數名稱
        if price_type.upper() == "MKT":
            try:
                order_kwargs["price_type"] = sj.constant.StockPriceType.MKT
            except Exception:  # noqa: BLE001
                order_kwargs["price_type"] = getattr(
                    sj.constant, "TFTStockPriceType", sj.constant.StockPriceType
                ).MKT
        else:
            try:
                order_kwargs["price_type"] = sj.constant.StockPriceType.LMT
            except Exception:  # noqa: BLE001
                order_kwargs["price_type"] = getattr(
                    sj.constant, "TFTStockPriceType", sj.constant.StockPriceType
                ).LMT

        if getattr(self.api, "stock_account", None) is not None:
            order_kwargs["account"] = self.api.stock_account

        order = self.api.Order(**order_kwargs)
        trade = self.api.place_order(contract, order)
        raw = str(trade)
        status = getattr(getattr(trade, "status", None), "status", None)
        status_text = str(status) if status is not None else "submitted"

        if self.store is not None:
            self.store.log_order(
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                status=status_text,
                simulation=use_sim,
                created_at=datetime.now(timezone.utc).isoformat(),
                raw=raw,
            )

        logger.info("下單完成 %s %s x%s status=%s", action, symbol, quantity, status_text)
        return OrderResult(ok=True, status=status_text, raw=raw, price=price)

    def dry_run_order(
        self, symbol: str, action: str, quantity: int = 1, price: float | None = None
    ) -> OrderResult:
        msg = f"[dry-run order] {action} {symbol} x{quantity} @ {price}"
        logger.info(msg)
        print(msg)
        if self.store is not None:
            self.store.log_order(
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                status="dry_run",
                simulation=True,
                created_at=datetime.now(timezone.utc).isoformat(),
                raw=msg,
            )
        return OrderResult(ok=True, status="dry_run", raw=msg, price=price)
