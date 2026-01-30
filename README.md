<p align="center">
  <img src="assets/banner.webp" alt="DexKeeper Banner" width="100%">
</p>

<p align="center">
  <img src="assets/icon.png" alt="DexKeeper Icon" width="128">
</p>

<p align="center">
  <a href="https://unlicense.org/"><img src="https://img.shields.io/badge/license-Unlicense-blue.svg" alt="License: Unlicense"></a>
  <a href="#"><img src="https://img.shields.io/badge/platform-Linux%20%7C%20Docker-lightgrey.svg" alt="Platform"></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.11-blue.svg" alt="Python 3.11"></a>
  <a href="https://github.com/westkitty"><img src="https://img.shields.io/badge/sponsor-WestKitty-ff69b4.svg" alt="Sponsor"></a>
  <a href="https://ko-fi.com/westkitty"><img src="https://img.shields.io/badge/Ko--fi-WestKitty-FF5E5B.svg" alt="Ko-fi"></a>
</p>

---

# DexKeeper_Bot

**High-performance Telegram community management bot with intelligent join verification, anti-spam flood protection, Zoom link formatting, admin dashboard, and moderation tools.**

DexKeeper is a production-ready Telegram bot designed to keep communities safe, organized, and ungovernable. Built with Python and SQLite, it combines enterprise-grade security with zero-friction administration.

## Key Features

- **Smart Join Verification** – CAPTCHA-based gating with customizable welcome messages
- **Real-Time Flood Detection** – Automatic rate limiting and temporary muting
- **Zoom Link Beautification** – Transforms raw Zoom URLs into styled cards (4 themes available)
- **Hierarchical Admin Dashboard** – Multi-tier access control with role-based permissions
- **Poll Creation & Broadcasting** – Engage your community with scheduled announcements
- **Lockdown Mode** – Instantly pause new member requests during emergencies
- **Word Filtering** – Auto-delete messages containing blacklisted terms
- **SQLite Persistence** – WAL mode for concurrent reads and zero data loss
- **CSV Exports** – Download complete user databases for analytics
- **Docker-Ready** – One-command deployment with health checks

## Installation

### Option A: Download Release

1. Visit the [Releases](https://github.com/westkitty/DexKeeper_Bot/releases) page
2. Download the latest `.zip` archive
3. Extract and configure your `.env` file:
   ```bash
   BOT_TOKEN=your_telegram_bot_token_here
   ADMIN_ID=your_telegram_user_id
   DB_PATH=data/dexkeeper.db
   ```
4. Run with Docker:
   ```bash
   cd scripts
   docker-compose up -d
   ```

### Option B: Build from Source

Clone the repository and build locally:

```bash
git clone https://github.com/westkitty/DexKeeper_Bot
cd DexKeeper_Bot
```

Create a `.env` file in the root directory:
```bash
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_telegram_user_id
DB_PATH=data/dexkeeper.db
```

Build and run with Docker:
```bash
cd scripts
docker-compose build
docker-compose up -d
```

**Verify the bot is running:**
```bash
docker-compose logs -f dexkeeper
```

You should see: `🚀 DexKeeper Systems Online`

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | ✅ | Your Telegram Bot API token from [@BotFather](https://t.me/BotFather) |
| `ADMIN_ID` | ✅ | Your Telegram user ID (get from [@userinfobot](https://t.me/userinfobot)) |
| `DB_PATH` | ❌ | SQLite database path (default: `data/dexkeeper.db`) |

### Admin Commands

- `/admin` – Open the hierarchical admin dashboard
- `/cancel` – Cancel the current admin operation

All other moderation actions (ban, unban, promote, lockdown, polls, broadcasts) are accessible via the interactive dashboard.

### Zoom Link Styles

DexKeeper can automatically detect and reformat Zoom links in 4 styles:

1. **👔 Professional** – Clean corporate aesthetic
2. **🦊 Mascot** – Playful Dexter branding
3. **⚡ Minimal** – One-liner with ID
4. **🔴 Disabled** – Pass through without formatting

Configure via: `/admin` → `🔧 Group Config` → `📝 Zoom Config`

## Architecture

```
DexKeeper_Bot/
├── Sources/DexKeeper_Bot/     # Core bot logic
│   ├── dexkeeper_bot.py       # Main application (720 lines)
│   ├── healthcheck.py         # Docker health probe
│   └── requirements.txt       # Python dependencies
├── scripts/                   # Deployment tools
│   ├── Dockerfile             # Production container
│   └── docker-compose.yml     # Orchestration config
├── templates/                 # Config templates (future)
├── assets/                    # Branding assets (future)
├── .env                       # Secrets (gitignored)
├── LICENSE                    # Unlicense (public domain)
├── VERSION                    # Semantic versioning
└── README.md                  # You are here
```

**Database Schema:**
- `settings` – Key-value config store
- `users` – Member registry with join timestamps
- `history` – Audit log for all moderation actions
- `pending_requests` – CAPTCHA verification queue
- `notes` – Per-user admin annotations
- `tags` – Custom user categorization

## Governance

Remain ungovernable so Dexter approves.

### Public Domain / Unlicense:

This project is dedicated to the public domain. You are free and encouraged to use, modify and distribute this software without any attribution required. You could even sell it... if you're a capitalist pig.

## Why Dexter?

*Dexter is a small, tricolor Phalène dog with floppy ears and a perpetually unimpressed expression... ungovernable, sharp-nosed and convinced he's the quality bar. Alert, picky, dependable and devoted to doing things exactly his way: if he's staring at you, assume you've made a mistake. If he approves, it means it works.*

---

<p align="center">
  <sub>Built with ❤️ by WestKitty | Inspected by Dexter 🐾</sub>
</p>
