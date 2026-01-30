# DexKeeper_Bot Installation Guide

## 1. Quick Start (The One-Liners)

**Linux / macOS / WSL2:**
Run this single block to download, configure, and start the bot instantly (assumes Docker is installed):

```bash
git clone https://github.com/westkitty/DexKeeper_Bot.git && cd DexKeeper_Bot && echo "BOT_TOKEN=ReplaceWithYourToken" > .env && cd scripts && docker-compose up -d --build
```

*(Note: You must edit `.env` with your actual token after this runs, then restart)*

---

## 2. Platform-Specific Setup

### 🍎 macOS
1.  **Install Docker**: Download [OrbStack](https://orbstack.dev/) (lighter) or Docker Desktop.
2.  **Open Terminal**.
3.  **Clone & Run**:
    ```bash
    git clone https://github.com/westkitty/DexKeeper_Bot.git
    cd DexKeeper_Bot
    echo "BOT_TOKEN=YOUR_ACTUAL_TOKEN_HERE" > .env
    cd scripts
    docker-compose up -d
    ```

### 🐧 Linux (Ubuntu/Debian)
1.  **Install Docker**:
    ```bash
    curl -fsSL https://get.docker.com | sh
    ```
2.  **Clone & Run**:
    ```bash
    git clone https://github.com/westkitty/DexKeeper_Bot.git
    cd DexKeeper_Bot
    echo "BOT_TOKEN=YOUR_ACTUAL_TOKEN_HERE" > .env
    cd scripts
    docker compose up -d
    ```

### 🪟 Windows (WSL2)
1.  **Install WSL2**: Open PowerShell as Admin and run `wsl --install`. Restart.
2.  **Install Docker Desktop**: Enable the "WSL2 Backend" option in settings.
3.  **Open Ubuntu Terminal** (from Start Menu).
4.  **Clone & Run**:
    ```bash
    git clone https://github.com/westkitty/DexKeeper_Bot.git
    cd DexKeeper_Bot
    echo "BOT_TOKEN=YOUR_ACTUAL_TOKEN_HERE" > .env
    cd scripts
    docker-compose up -d
    ```

---

## 3. How to Build This (For the curious)

So you want to know how this actually works? Here is the breakdown, plain and simple.

**1. The "Box" (Docker)**
Think of this bot as a fully furnished room inside a shipping container.
*   **The Container (Docker Image)**: We froze a copy of Linux, Python 3.11, and all the bot's libraries into a file. This guarantees it works exactly the same on your computer as it does on mine. No "it works on my machine" excuses.
*   **The Blueprint (Dockerfile)**: This is the recipe for the container. It says: "Start with Python, add these files, install these libraries."

**2. The Brain (Python)**
*   The code lives in `Sources/DexKeeper_Bot/dexkeeper_bot.py`.
*   It talks to Telegram's servers using an **API Token**. This is like a password that tells Telegram "I am DexKeeper, let me read messages."

**3. The Memory (SQLite)**
*   The bot needs to remember who verified, who got banned, and what settings you changed.
*   It saves this into a single file: `data/dexkeeper.db`. This is why we "mount" a volume in Docker—so that even if you destroy the container (the shipping crate), the notebook inside (database) is kept safe on your actual hard drive.

**Summary:**
You download the recipe (`git clone`), you verify your identity (`.env`), and you tell the shipyard to build and launch your container (`docker-compose up`). Done.
