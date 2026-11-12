# NEWCAFE Telegram Bot + Mini App

NEWCAFE is a demo coffee-shop project built with Python and **aiogram 3**. The bot uses Telegram long polling, while the same Railway service serves `index.html` over HTTPS. The Mini App can send a demo order back to the bot with `Telegram.WebApp.sendData`.

## Features

- Uzbek-language `/start`, `/help`, and administrator-only `/admin` commands.
- Product catalogue, per-user in-memory cart, demo checkout, promotion, about, and contact buttons.
- Telegram Mini App button using `MINI_APP_URL` (or Railway's public domain when available).
- Mini App demo orders are validated and sent to the configured administrator.
- `/` serves `index.html`; `/health` is available for Railway health checks.
- No database, real payment, or real delivery. In-memory carts and orders are not persisted.

## Project structure

```text
NEWCAFE/
├── main.py
├── admin.py
├── index.html
├── requirements.txt
├── railway.toml
├── .gitignore
├── README.md
└── assets/
    ├── newcafe_banner.jpg
    ├── newcafe_products.jpg
    └── .gitkeep
```

The existing `assets/` files are retained. The repository did not contain `index.html` when inspected, so this project adds one rather than replacing an existing Mini App. The existing bot used `python-telegram-bot`; it has been migrated to the requested aiogram 3 framework while retaining the existing demo shop sections.

## Requirements

- Python 3.10 or later.
- A Telegram bot token from [@BotFather](https://t.me/BotFather).
- Your numeric Telegram user ID for `ADMIN_ID`.
- An HTTPS public URL for the deployed app, set as `MINI_APP_URL`.

Never commit `.env` or paste a bot token into source code, issues, or chat. If a token was ever exposed, revoke it through BotFather and replace it.

## Run locally

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Set environment variables in your shell (substitute your own values; do not include angle brackets):

```bash
# macOS/Linux
export BOT_TOKEN="your_botfather_token"
export ADMIN_ID="your_numeric_telegram_user_id"
export MINI_APP_URL="https://your-public-https-host"
python main.py
```

```powershell
# Windows PowerShell
$env:BOT_TOKEN = "your_botfather_token"
$env:ADMIN_ID = "your_numeric_telegram_user_id"
$env:MINI_APP_URL = "https://your-public-https-host"
python main.py
```

The process listens on `PORT` (defaults to `8080`) and polls Telegram updates. For Telegram's Mini App button and `sendData`, use an HTTPS URL and open the Mini App from the bot's persistent **🌐 NEWCAFE Mini App** keyboard button. The project deliberately uses a reply-keyboard Web App button because Telegram's `sendData` is supported for Mini Apps launched from a keyboard button.

If `MINI_APP_URL` is unset, the bot tries `RAILWAY_PUBLIC_DOMAIN`; otherwise it serves the page locally but does not show the Mini App launch button.

## Deploy to Railway from GitHub

1. Push this repository to GitHub. Confirm `main.py`, `admin.py`, `index.html`, `requirements.txt`, and `railway.toml` are in the repository root.
2. Sign in to [Railway](https://railway.app/) and choose **New Project → Deploy from GitHub repo**.
3. Authorize Railway to access GitHub if prompted, then select the NEWCAFE repository and its deployment branch.
4. Open the Railway service's **Variables** tab and add:
   - `BOT_TOKEN` — token from BotFather (secret; do not put it in GitHub).
   - `ADMIN_ID` — your numeric Telegram user ID.
   - `MINI_APP_URL` — add after the service has a public domain, as described below.
5. In Railway, open **Settings → Networking** and generate a public domain. Railway provides HTTPS for this domain.
6. Set `MINI_APP_URL` to the full root URL, for example `https://your-service.up.railway.app` (use the actual domain Railway assigned, not this example).
7. Check the deployment logs and wait for the service to become healthy. The app serves `/health` and starts the Telegram polling bot in the same process.
8. Open your bot in Telegram and send `/start`. Test the menu buttons, open **🌐 NEWCAFE Mini App**, change item quantities, and submit a demo order. The configured admin Telegram account should receive the order.

Railway normally redeploys when new commits arrive on the connected branch. You can also trigger a redeploy from the Railway service dashboard. Do not run multiple active copies of this polling bot with the same token; they may conflict while polling updates.

## Environment variables

| Name | Required | Description |
| --- | --- | --- |
| `BOT_TOKEN` | Yes | Telegram BotFather token. Keep it secret. |
| `ADMIN_ID` | Yes | Numeric Telegram user ID allowed to use `/admin` and receive Mini App demo orders. |
| `MINI_APP_URL` | Recommended in production | Public HTTPS URL of this service. If absent, the app uses `RAILWAY_PUBLIC_DOMAIN` when available. |
| `PORT` | No | HTTP port provided by Railway; defaults to `8080` locally. |

## Notes and limitations

- Mini App order totals are recalculated by the bot from its own product prices; client-supplied prices are never trusted.
- `/admin` is a small access-controlled status/help command, not a full management dashboard.
- Demo orders and carts are not stored. Restarting the process loses in-memory carts, and no order history is available.
- The example contact details and product prices are placeholders for a demo.
- A successful GitHub update does not itself prove that Railway deployment or Telegram runtime behavior has been tested. Verify them in the Railway logs and Telegram as described above.
