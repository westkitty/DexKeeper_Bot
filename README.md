![DexKeeper Bot Banner](assets/DexKeeper_Bot_banner.webp)

<div align="center">
  <img src="assets/DexKeeper_Bot_icon.png" width="128" height="128" />
</div>

<div align="center">

![License](https://img.shields.io/badge/License-Unlicense-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Docker_|_Python-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11-yellow.svg)
[![Sponsor](https://img.shields.io/badge/Sponsor-pink?style=flat-square&logo=github-sponsors)](https://github.com/sponsors/westkitty)
[![Ko-Fi](https://img.shields.io/badge/Ko--fi-Support%20My%20Work-FF5E5B?style=flat-square&logo=ko-fi&logoColor=white)](https://ko-fi.com/westkitty)

</div>

# DexKeeper_Bot

**DexKeeper** is a high-performance, privacy-focused telegram bot designed to manage communities with minimal friction. It combines automated moderation, engagement tools, and security features into a single containerized application that you own 100%.

Unlike cloud bots, **you host this yourself**. Your data, your rules, your hardware.

---

## 🌟 Features

### 🛡️ Security & Moderation
- **"I Am Human" Captcha**: Automatically restricts new members until they verify they are human, stopping bot spam instantly.
- **Lockdown Mode**: Instantly reject all new join requests during raid attacks.
- **Bad Word Filter**: define a custom list of prohibited words; messages containing them are auto-deleted.
- **Flood Gate**: Auto-mutes users who spam messages too quickly (5 messages in < 2 seconds).

### 📢 Engagement Tools
- **Welcome Messages**: Customizable greeting for verified members.
- **Polls**: Create and post native Telegram polls directly from the admin panel.
- **Broadcast**: Send a message to all users who have DM'd the bot (great for announcements).
- **Scheduled Messages**: Set a message to be sent to a group after X minutes.
- **Forum Topics**: Create new topics in forum-enabled groups.

### 🎥 Utilities
- **Zoom Enforcer**: Detects raw Zoom links and converts them into beautiful, clickable cards (Professional, Mascot, or Minimal styles). prevents messy link clutter.
- **User Management**: View, Ban, Unban, and Promote users from a GUI.
- **CSV Export**: Download a full list of your user database as a CSV file.

---

## 📋 Prerequisites

Before you start, you need two things:
1.  **A Computer**: Any PC (Windows, Mac, or Linux) that can run Docker.
2.  **A Telegram Account**: To create the bot and be its admin.

---

## 🤖 Phase 1: Get Your Bot Token

You need to tell Telegram "I am making a bot" and get a key to control it.

1.  Open Telegram and search for **@BotFather**.
2.  Click **Start**.
3.  Type `/newbot` and press Enter.
4.  **Name your bot** (e.g., "My Super Group Manager").
5.  **Choose a username** (must end in `bot`, e.g., `MySuperManager_bot`).
6.  BotFather will reply with a long string of text under "Use this token to access the HTTP API:".
    *   **COPY THIS TOKEN.** It looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`.
    *   *Treat this like a password. Do not share it.*

---

## 💻 Phase 2: Installation Guide

### Option A: Download Pre-Built Release (Easiest)

**[📥 Download the latest release (.zip)](https://github.com/westkitty/DexKeeper_Bot/releases/latest)**

1. Download `DexKeeper_Bot_v0.1.0.zip` from the Releases page.
2. Extract the ZIP file.
3. Continue to "Configure the Bot" below.

### Option B: Clone from Source

We use **Docker** to make this easy. If you don't know what Docker is, think of it as a "program player". We give you the cartridge (this code), and Docker plays it exactly the same on every computer.

### Step 1: Install Docker
- **Windows**: Download [Docker Desktop](https://www.docker.com/products/docker-desktop/).
- **Mac**: Download [OrbStack](https://orbstack.dev/) (Recommended, faster) or Docker Desktop.
- **Linux**: Run `curl -fsSL https://get.docker.com | sh`.

### Step 2: Download DexKeeper
1.  Click the **Code** button (green) on this page -> **Download ZIP**.
2.  Unzip the folder somewhere easy to find (like your Desktop).

### Step 3: Configure the Bot
1.  Open the `DexKeeper_Bot` folder.
2.  Copy `.env.example` to `.env`:
    ```bash
    cp .env.example .env
    ```
3.  Open `.env` with Notepad or TextEdit.
4.  Replace the placeholder with your actual bot token:
    ```
    BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
    ```
5.  (Optional) Add your Telegram User ID to become admin:
    ```
    ADMIN_ID=123456789
    ```
6.  Save and close.

### Step 4: Run It
1.  **Open Terminal** (Mac/Linux) or **PowerShell** (Windows).
2.  Type `cd ` (with a space) and drag the `DexKeeper_Bot` folder into the window. Press Enter.
    *   It should look like: `cd /Users/you/Desktop/DexKeeper_Bot`
3.  Run this command to start:
    ```bash
    cd scripts && docker-compose up -d --build
    ```
4.  Wait for `Started` or `Running`. Your bot is now online!

### Alternative: Running Manually (Without Docker)

If you prefer to run Python directly:

1.  **Install Python 3.11+**.
2.  **Install Requirements**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure**: Create `.env` as shown above.
4.  **Run**:
    ```bash
    python3 Sources/DexKeeper_Bot/dexkeeper_bot.py
    ```

---

## 🛸 Phase 3: Setup on Telegram

1.  **Find your bot**: Search for your bot's username in Telegram.
2.  **Start it**: Click **Start** in the DM.
    *   *Note: Since you are the owner, this registers you as Admin.*
3.  **Add to Group**:
    *   Go to your Group Info -> **Add Members**.
    *   Search for your bot and add it.
4.  **Promote to Admin**:
    *   In Group Info -> **Edit** -> **Administrators** -> **Add Admin**.
    *   Select your bot.
    *   **CRITICAL**: Give it all permissions (Delete Messages, Ban Users, Invite Users, Pin Messages).
    *   Save.

---

## 🎮 Phase 4: How to Use

Everything is controlled via the **Admin Panel**.

1.  Go to the **Direct Message (DM)** with your bot.
2.  Type `/admin`.
3.  A menu will appear with buttons:
    *   **👥 User Management**: Ban/Unban tools, Export CSV.
    *   **📢 Engagement**: Create Polls, Schedule Messages, Broadcasts.
    *   **🔧 Group Config**: Configure Zoom style (Professional/Mascot/Minimal).
    *   **🛡️ Security**: Lockdown mode, Word filters.

**Example: Creating a Poll**
1.  Click **📢 Engagement**, then **📊 Create Poll**.
2.  The bot will ask for the Question. Type it in chat.
3.  The bot will ask for Options (comma separated). Type: `Yes, No, Maybe`.
4.  Done! The poll posts to the group.

---

## Governance

Remain ungovernable so Dexter approves.

### **Public Domain / Unlicense:**

This project is dedicated to the public domain. You are free and encouraged to use, modify and distribute this software without any attribution required.
You could even sell it... if you're a capitalist pig.

---

## Why Dexter?

*Dexter is a small, tricolor Phalène dog with floppy ears and a perpetually unimpressed expression... ungovernable, sharp-nosed and convinced he’s the quality bar. Alert, picky, dependable and devoted to doing things exactly his way: if he’s staring at you, assume you’ve made a mistake. If he approves, it means it works.*
