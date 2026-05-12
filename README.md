# Price Monitor Pro

An automated price monitoring tool that tracks Amazon product prices
using Selenium, logs data to Google Sheets, and sends instant Telegram
alerts when a price drops below your target.

---

## Features

- Selenium WebDriver scrapes live prices from Amazon
- Handles JavaScript-heavy pages and anti-bot detection
- Forces USD currency regardless of your location
- Logs every price check to Google Sheets automatically
- Instant Telegram alert when price drops below target
- Alert cooldown — won't spam if price stays below target
- Monitors multiple products simultaneously
- Clean shutdown with Ctrl+C

---

## Tech Stack

- Python 3.13
- Selenium & WebDriver Manager
- Google Sheets API via gspread
- Telegram Bot API
- Python-dotenv

---

## How It Works

1. Selenium launches a headless Chrome browser
2. Loads Amazon with USD currency forced via cookie
3. Extracts the current price using CSS selectors
4. Logs the result to Google Sheets with timestamp
5. Sends a Telegram alert if price is below target
6. Waits one hour and repeats

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/JeanMrc/price-monitor-pro
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Google Sheets API
- Go to Google Cloud Console
- Create a project and enable Google Sheets API and Google Drive API
- Create a Service Account and download the JSON key
- Rename it to `credentials.json` and place it in the project folder
- Create a blank Google Sheet and share it with the service account email as Editor

### 4. Telegram Bot
- Open Telegram and search `@BotFather`
- Send `/newbot` and follow the prompts
- Copy the token
- Send your bot a message then run:
```bash
python -c "import requests; r = requests.get('https://api.telegram.org/bot/getUpdates'); print(r.json())"
```
- Copy the `id` value from the `chat` field — that's your Chat ID

### 5. Environment Variables
Create a `.env` file:
TELEGRAM_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
GOOGLE_SHEET_ID=your_sheet_id_here

### 6. Add Products
Edit the `PRODUCTS` list in `monitor.py`:
```python
PRODUCTS = [
    {
        "name":         "ASUS ROG Flow Gaming Laptop",
        "url":          "https://www.amazon.com/dp/B0DW238TXK/",
        "target_price": 1500.00,
    }
]
```

### 7. Run
```bash
python monitor.py
```

---

## Google Sheets Output

| Timestamp           | Product              | Price  | Target | Alert |
|---------------------|----------------------|--------|--------|-------|
| 2026-05-12 07:18:00 | ASUS ROG Flow Laptop | 2707.0 | 1500.0 | NO    |
| 2026-05-12 07:25:00 | ASUS ROG Flow Laptop | 2707.0 | 3000.0 | YES   |

---

## Technical Challenges Solved

**1. Amazon location-based currency**
Amazon serves prices in local currency based on IP location. Solved
by setting the `i18n-prefs` cookie to USD before loading the product
page, forcing consistent USD pricing regardless of where the script runs.

**2. JavaScript-heavy page rendering**
Amazon prices are rendered dynamically. Solved by using Selenium
WebDriver with explicit waits and multiple CSS selector fallbacks
to reliably extract the price element.

**3. Anti-bot detection**
Headless browsers are often detected and blocked. Solved by spoofing
the user agent, disabling automation flags, and adding realistic
page load delays.

---

## Project Structure
price-monitor-pro/
├── monitor.py          — main script
├── requirements.txt    — dependencies
├── .env                — credentials (not tracked)
├── credentials.json    — Google service account (not tracked)
└── .gitignore

