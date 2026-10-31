#!/usr/bin/env bash
# 可用 crontab 呼叫，例如：
# 30 16 * * 1-5 cd /path/to/repo && ./scripts/run_daily.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
python -m tw_stock.cli fetch
python -m tw_stock.cli alert
