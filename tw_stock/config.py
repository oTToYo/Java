"""載入設定與環境變數。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "settings.yaml"
ENV_PATH = ROOT / ".env"


def load_env() -> None:
    load_dotenv(ENV_PATH)


def project_root() -> Path:
    return ROOT


def load_settings(path: Path | None = None) -> dict[str, Any]:
    load_env()
    cfg_path = path or CONFIG_PATH
    with cfg_path.open(encoding="utf-8") as f:
        settings = yaml.safe_load(f) or {}

    # 環境變數覆寫敏感設定
    settings.setdefault("finmind", {})
    settings.setdefault("line", {})
    settings.setdefault("sinopac", {})

    if token := os.getenv("FINMIND_TOKEN"):
        settings["finmind"]["token"] = token

    if token := os.getenv("LINE_CHANNEL_ACCESS_TOKEN"):
        settings["line"]["channel_access_token"] = token
    if user_id := os.getenv("LINE_USER_ID"):
        settings["line"]["user_id"] = user_id

    if api_key := os.getenv("SHIOAJI_API_KEY"):
        settings["sinopac"]["api_key"] = api_key
    if secret := os.getenv("SHIOAJI_SECRET_KEY"):
        settings["sinopac"]["secret_key"] = secret
    if person_id := os.getenv("SHIOAJI_PERSON_ID"):
        settings["sinopac"]["person_id"] = person_id
    if ca_passwd := os.getenv("SHIOAJI_CA_PASSWD"):
        settings["sinopac"]["ca_passwd"] = ca_passwd
    if ca_path := os.getenv("SHIOAJI_CA_PATH"):
        settings["sinopac"]["ca_path"] = ca_path

    sim = os.getenv("SHIOAJI_SIMULATION")
    if sim is not None:
        settings["sinopac"]["simulation"] = sim.strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    live = os.getenv("ENABLE_LIVE_TRADING")
    if live is not None:
        settings["sinopac"]["enable_live_trading"] = live.strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    db = os.getenv("STOCK_DB_PATH")
    if db:
        settings.setdefault("storage", {})["db_path"] = db

    return settings


def resolve_path(path: str | Path) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    return p
