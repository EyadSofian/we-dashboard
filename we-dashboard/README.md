# WE Quota Dashboard

Production-ready self-hosted dashboard that tracks **WE / TE Data** internet quota for multiple landlines, stores usage history, forecasts when the quota will run out, and fires Telegram alerts via n8n when usage crosses thresholds.

**Stack:** FastAPI · httpx · APScheduler · SQLAlchemy (SQLite) · React + Vite + Tailwind · Recharts · Single Dockerfile · Railway-ready.

---

## Features

- 🔐 **Multi-account**: Track multiple WE landlines from one dashboard
- 📊 **Live snapshot**: Used / Remaining / Total / Usage % / Renewal countdown
- 📈 **History tracking**: Auto-poll every 15 min (configurable) into SQLite
- 📉 **Forecast**: Linear regression on the current quota cycle → "days until exhaust" with confidence rating
- 🔔 **Threshold alerts**: Webhook fires once per quota cycle, routed via n8n to Telegram/WhatsApp/Email
- 🔒 **Encrypted credentials**: Passwords stored with Fernet (key derived from `SECRET_KEY`)
- 🧪 **Credential verification**: New accounts are validated against the WE API before saving
- 🎨 **Modern UI**: Dark dashboard, gauge ring, trend chart, account switcher

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     Single Container                           │
│                                                                │
│  React SPA  ───┐                                               │
│  (dist)        │                                               │
│                ▼                                               │
│          ┌──────────┐    ┌────────────┐    ┌──────────────┐    │
│          │ FastAPI  │───▶│ APScheduler│───▶│ WEClient     │    │
│          │ /api/*   │    │ every 15m  │    │ httpx.async  │    │
│          │ + SPA    │    └────┬───────┘    └──────┬───────┘    │
│          │ serve    │         │                   │            │
│          └────┬─────┘         ▼                   ▼            │
│               │         ┌─────────────┐    api-my.te.eg        │
│               │         │  SQLite     │                        │
│               └────────▶│  /data/we.db│                        │
│                         └──────┬──────┘                        │
│                                │                               │
│                         AlertConfig                            │
│                                │                               │
│                                ▼                               │
│                       n8n webhook (external)                   │
│                                │                               │
│                                ▼                               │
│                       Telegram / WhatsApp                      │
└────────────────────────────────────────────────────────────────┘
```

**Why polling, not Selenium**: WE exposes the same internal JSON API that `my.te.eg` uses. The 4-step flow (`querySysParams` → `userAuthenticate` → `getSubscribedOfferings` → `queryFreeUnit`) is fully reversed in `backend/app/we_client.py`.

---

## Quick Start (Local)

```bash
git clone <this-repo> we-dashboard && cd we-dashboard

cp .env.example .env
# Edit .env: set SECRET_KEY (32+ chars), ADMIN_PASSWORD, N8N_WEBHOOK_URL

docker compose up --build
```

Open **http://localhost:8000** → login with `ADMIN_PASSWORD` → **Accounts** → add your landline (with leading `0`) + WE password.

The scheduler runs immediately on startup, then every `POLL_INTERVAL_MINUTES`.

---

## Deploy to Railway

### 1. Push the repo to GitHub

```bash
git init && git add . && git commit -m "init"
git remote add origin https://github.com/<you>/we-dashboard.git
git push -u origin main
```

### 2. Create a Railway project

- Railway → **New Project** → **Deploy from GitHub** → pick the repo
- Railway auto-detects `railway.toml` and the `Dockerfile`

### 3. Attach a volume for SQLite persistence

- Project → **+ New** → **Volume** → mount path `/data` (size: 1 GB is plenty)

### 4. Environment variables

In Railway → service → **Variables**, set:

| Key | Value |
|---|---|
| `SECRET_KEY` | `openssl rand -hex 32` |
| `ADMIN_PASSWORD` | strong password to log into the dashboard |
| `DATABASE_URL` | `sqlite+aiosqlite:////data/we.db` |
| `N8N_WEBHOOK_URL` | `https://n8n.engosoft.com/webhook/we-quota-alert` |
| `POLL_INTERVAL_MINUTES` | `15` |

### 5. Deploy

Railway builds the Dockerfile (Node stage → Python stage), runs `uvicorn`, exposes `${PORT}`. Healthcheck hits `/api/health`.

### 6. (Optional) Swap SQLite for Postgres

If you'd rather not deal with a volume:

- Railway → **+ New** → **Database** → **PostgreSQL**
- Copy the `DATABASE_URL` Railway generates, prefix the driver: `postgresql+asyncpg://...`
- Add `asyncpg` to `backend/requirements.txt`, redeploy.

---

## Importing the n8n Telegram workflow

1. Open n8n → **Workflows** → **Import from File** → pick `n8n/we-quota-alert-telegram.json`
2. Open the **Send Telegram** node → set your Telegram credential (BotFather token)
3. In n8n → **Variables**, set `TELEGRAM_CHAT_ID` to your chat/group/channel ID
4. Activate the workflow → copy the production webhook URL
5. Paste that URL into the dashboard's `N8N_WEBHOOK_URL` env var and redeploy

The message is rendered in Arabic with a progress bar, severity emoji, renewal countdown, and Cairo-timezone formatting.

**Test the webhook locally:**

```bash
curl -X POST $N8N_WEBHOOK_URL -H 'Content-Type: application/json' -d '{
  "event": "we.quota.threshold",
  "account_id": 1,
  "label": "Home",
  "landline": "0234567891",
  "customer_name": "EYAD SOFIAN",
  "offer_name": "VDSL 140GB",
  "threshold_pct": 90,
  "usage_pct": 91.42,
  "used_gb": 128.0,
  "remain_gb": 12.0,
  "total_gb": 140.0,
  "expire_time_iso": "2026-06-01T00:00:00Z",
  "snapshot_taken_at": "2026-05-13T18:45:12Z"
}'
```

---

## API Reference

All routes (except `/api/health` and `/api/auth/login`) require `Authorization: Bearer <jwt>`.

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/login` | Exchange `ADMIN_PASSWORD` for JWT |
| GET | `/api/accounts` | List tracked landlines |
| POST | `/api/accounts` | Add landline (verifies against WE before saving) |
| PATCH | `/api/accounts/{id}` | Update label / pause / rotate password |
| DELETE | `/api/accounts/{id}` | Remove account + cascade history |
| GET | `/api/dashboard/{id}` | Latest snapshot + forecast |
| GET | `/api/history/{id}?days=30` | Time series |
| POST | `/api/refresh/{id}` | Force immediate poll |
| GET | `/api/alerts/{id}` | List thresholds |
| POST | `/api/alerts/{id}` | Add threshold (e.g. `{threshold_pct: 90}`) |
| PATCH | `/api/alerts/{id}` | Enable/disable/update |
| DELETE | `/api/alerts/{id}` | Remove threshold |
| GET | `/api/alerts/logs/{id}` | Last 50 fires |

OpenAPI docs auto-served at `/docs`.

---

## Operational notes

- **First snapshot**: the scheduler runs once at startup. Force one any time with the **Refresh** button.
- **Forecast confidence**: low (<3 days of samples) / medium (3–7d) / high (>7d). It picks samples within the current quota cycle (same `effective_time`) so renewal resets don't poison the regression.
- **Alert dedupe**: each threshold fires once per quota cycle. After renewal (`effective_time` changes), all thresholds rearm.
- **Auth errors disable polling**: if WE rejects credentials (password changed), the account is auto-paused. Re-enable from the Accounts page after updating the password.
- **IP location matters**: WE may rate-limit or block non-Egyptian IPs. Railway's edges are usually fine, but if you see auth errors from the cloud and not locally, that's why.
- **No CAPTCHA today**: if WE ever adds one, the client will fail with `WEAuthError` and the account auto-pauses. Update the client if/when that happens.

---

## Project layout

```
we-dashboard/
├── Dockerfile               # multi-stage: Node → Python
├── docker-compose.yml
├── railway.toml
├── .env.example
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py          # FastAPI + SPA serve
│       ├── config.py
│       ├── db.py
│       ├── models.py
│       ├── schemas.py
│       ├── security.py      # Fernet + JWT
│       ├── deps.py
│       ├── we_client.py     # ⭐ reverse-engineered WE API
│       ├── forecast.py
│       ├── alerts.py        # webhook dispatcher
│       ├── scheduler.py     # APScheduler jobs
│       └── routers/
│           ├── auth.py
│           ├── accounts.py
│           ├── quota.py
│           └── alerts.py
├── frontend/                # Vite + React + TS + Tailwind + Recharts
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── src/
│       ├── api/client.ts
│       ├── components/
│       └── pages/
└── n8n/
    └── we-quota-alert-telegram.json
```

---

## Roadmap ideas

- Switch SQLite → Postgres (single `DATABASE_URL` swap, add `asyncpg`)
- WhatsApp Cloud API path in the same n8n workflow
- Daily/weekly digest message instead of just threshold pings
- Export history as CSV
- 2FA on dashboard login

---

## Disclaimer

This is **not** affiliated with or endorsed by Telecom Egypt. It calls the public-facing internal API used by `my.te.eg` for personal/internal monitoring use only. Don't deploy this against accounts you don't own.

**License:** MIT
