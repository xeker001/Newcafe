# Vercel deploy notes for NEWCAFE Mini App

This folder contains only the static Telegram Mini App. The Telegram bot (`main.py`) must stay deployed on Railway; do not deploy the repository root as a Python project on Vercel.

## Configure Vercel

1. Import the GitHub repository `xeker001/Newcafe` into Vercel.
2. In the Vercel project, open **Settings → Build and Deployment**.
3. Set **Root Directory** to `miniapp` and save. Leave Framework Preset as **Other**; no build command or output directory is needed for this static `index.html`.
4. Redeploy the project.
5. Open the Vercel deployment URL and confirm the NEWCAFE page loads.
6. In Railway, set `MINI_APP_URL` to the complete Vercel HTTPS URL, then redeploy the bot.

The repository's original root-level `index.html` is intentionally kept. `miniapp/index.html` is a copy used for the Vercel static deployment.

## Telegram order handoff

Open the Mini App through the bot's Telegram Web App keyboard button, not by opening the Vercel URL directly in a browser. `Telegram.WebApp.sendData` works from the Telegram Mini App context. The receiving bot must be running on Railway with `BOT_TOKEN` and `ADMIN_ID` configured.
