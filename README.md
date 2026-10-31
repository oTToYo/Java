# 台灣股市自動化系統

每天自動抓取台股日線、畫 K 線與技術指標、依條件推播 LINE，並可串接永豐金 **Shioaji** API 自動下單。

> **風險提醒**：自動下單會動用真實資金。預設為 **模擬／dry-run**；實盤需同時關閉模擬並顯式開啟 `ENABLE_LIVE_TRADING=true`。本專案不構成投資建議。

## 功能

| 模組 | 說明 |
| --- | --- |
| 日資料抓取 | `yfinance` 歷史回補 + 證交所 OpenAPI 當日行情；可選 FinMind |
| 本地儲存 | SQLite（`data/stocks.db`） |
| K 線圖 | `mplfinance` 產出含 MA / RSI 的圖檔 |
| 指標 | MA、RSI、MACD、KD |
| LINE 通知 | **Messaging API** 推播（LINE Notify 已於 2025-03-31 停用） |
| 永豐下單 | Shioaji；預設模擬，可依告警規則自動下單 |
| 排程 | APScheduler 或 crontab |
| 儀表板 | Streamlit 檢視 K 線與指標 |

## 快速開始

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 編輯 config/settings.yaml 的 watchlist / alerts
```

### 抓資料、看指標、畫圖

```bash
python -m tw_stock.cli fetch
python -m tw_stock.cli indicators 2330
python -m tw_stock.cli chart 2330
```

### 檢查告警（預設 dry-run，只印出訊息）

```bash
python -m tw_stock.cli alert
python -m tw_stock.cli notify-test --message "測試"
```

### 啟動儀表板 / 排程

```bash
python -m tw_stock.cli dashboard
python -m tw_stock.cli schedule
```

或用 crontab（台灣時間收盤後）：

```cron
30 16 * * 1-5 /path/to/repo/scripts/run_daily.sh
```

## LINE Messaging API 設定

1. 到 [LINE Developers](https://developers.line.biz/) 建立 Provider 與 **Messaging API** Channel。  
2. 取得 **Channel access token**，填入 `.env` 的 `LINE_CHANNEL_ACCESS_TOKEN`。  
3. 加官方帳號為好友，透過 webhook 取得自己的 `userId`，填入 `LINE_USER_ID`。  
4. 將 `config/settings.yaml` 的 `line.dry_run` 設為 `false`，或設環境變數後執行：

```bash
python -m tw_stock.cli notify-test --live --message "台股機器人上線"
```

## 永豐 Shioaji 下單

1. 開立永豐金證券帳戶，簽署 API 風險預告書並申請 API Key。  
2. 下載電子憑證 `Sinopac.pfx` 放到 `certs/`（路徑可在 `.env` 調整）。  
3. 填入：

```env
SHIOAJI_API_KEY=...
SHIOAJI_SECRET_KEY=...
SHIOAJI_PERSON_ID=...
SHIOAJI_CA_PASSWD=...
SHIOAJI_CA_PATH=certs/Sinopac.pfx
SHIOAJI_SIMULATION=true
ENABLE_LIVE_TRADING=false
```

4. 手動下單（未開實盤時自動 dry-run）：

```bash
python -m tw_stock.cli order 2330 Buy --qty 1 --dry-run
```

5. 若要「指標觸發後自動下單」，在 `config/settings.yaml`：

```yaml
sinopac:
  auto_trade:
    enabled: true
    buy_on: ["RSI 超賣", "MACD 黃金交叉"]
    sell_on: ["RSI 超買", "MACD 死亡交叉"]
    quantity: 1
    price_type: MKT
```

實盤條件（缺一不可）：

- `SHIOAJI_SIMULATION=false`
- `ENABLE_LIVE_TRADING=true`
- 憑證 `activate_ca` 成功

## 告警規則範例

編輯 `config/settings.yaml` 的 `alerts.rules`：

```yaml
- name: "RSI 超賣"
  indicator: rsi
  op: "<"
  value: 30
  message: "{symbol} RSI={value:.1f} 進入超賣區"
- name: "站上月線"
  indicator: close_above_ma
  ma: 20
  message: "{symbol} 收盤 {close:.2f} 站上 MA20 {ma:.2f}"
- name: "MACD 黃金交叉"
  indicator: macd_golden_cross
  message: "{symbol} MACD 出現黃金交叉"
```

支援指標：`rsi`、`close_above_ma`、`close_below_ma`、`macd_golden_cross`、`macd_death_cross`、`kd_golden_cross`、`kd_death_cross`。

## 專案結構

```
tw_stock/
  cli.py              # 命令列
  dashboard.py        # Streamlit
  config.py
  data/               # 抓取與 SQLite
  indicators/         # 技術指標
  charts/             # K 線
  notify/             # LINE
  trading/            # 永豐 Shioaji
  alerts/             # 規則引擎
  jobs/               # 每日任務與排程
config/settings.yaml
```

## 測試

```bash
pytest -q
```
