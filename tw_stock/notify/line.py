"""LINE Messaging API 推播（取代已停用的 LINE Notify）。"""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib import error, request

logger = logging.getLogger(__name__)

PUSH_URL = "https://api.line.me/v2/bot/message/push"


class LineNotifier:
    def __init__(
        self,
        channel_access_token: str = "",
        user_id: str = "",
        dry_run: bool = True,
    ):
        self.token = channel_access_token or ""
        self.user_id = user_id or ""
        self.dry_run = dry_run

    @classmethod
    def from_settings(cls, settings: dict[str, Any]) -> "LineNotifier":
        line = settings.get("line") or {}
        return cls(
            channel_access_token=line.get("channel_access_token", ""),
            user_id=line.get("user_id", ""),
            dry_run=bool(line.get("dry_run", True)),
        )

    def send_text(self, message: str) -> bool:
        if self.dry_run:
            logger.info("[LINE dry-run] %s", message)
            print(f"[LINE dry-run] {message}")
            return True

        if not self.token or not self.user_id:
            logger.error("缺少 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_USER_ID")
            return False

        body = json.dumps(
            {
                "to": self.user_id,
                "messages": [{"type": "text", "text": message[:4500]}],
            }
        ).encode("utf-8")

        req = request.Request(
            PUSH_URL,
            data=body,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=20) as resp:
                ok = 200 <= resp.status < 300
                if not ok:
                    logger.error("LINE 推播失敗 status=%s", resp.status)
                return ok
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            logger.error("LINE HTTPError %s: %s", exc.code, detail)
            return False
        except error.URLError as exc:
            logger.error("LINE URLError: %s", exc)
            return False
