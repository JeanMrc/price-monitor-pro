import os
import time
import json
import argparse
import requests
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import gspread
from google.oauth2.service_account import Credentials

# ─────────────────────────────────────────
# Config
# ─────────────────────────────────────────
load_dotenv()

TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GOOGLE_SHEET_ID  = os.getenv("GOOGLE_SHEET_ID")

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
PRODUCTS_FILE = os.path.join(BASE_DIR, "products.json")
CHECK_EVERY   = 3600

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ─────────────────────────────────────────
# Products File
# ─────────────────────────────────────────
def load_products():
    if not os.path.exists(PRODUCTS_FILE):
        return []
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)

def save_products(products):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=4)

def add_product(name, url, target_price):
    products = load_products()
    for p in products:
        if p["name"].lower() == name.lower():
            print(f"Product '{name}' already exists.")
            return
    products.append({
        "name":         name,
        "url":          url,
        "target_price": float(target_price)
    })
    save_products(products)
    print(f"Added: {name} — Target: ${target_price}")

def remove_product(name):
    products = load_products()
    updated  = [p for p in products if p["name"].lower() != name.lower()]
    if len(updated) == len(products):
        print(f"Product '{name}' not found.")
        return
    save_products(updated)
    print(f"Removed: {name}")

def list_products():
    products = load_products()
    if not products:
        print("No products tracked yet.")
        return
    print("\nTracked Products:")
    print("-" * 50)
    for i, p in enumerate(products, 1):
        print(f"{i}. {p['name']}")
        print(f"   URL   : {p['url']}")
        print(f"   Target: ${p['target_price']}")
    print("-" * 50)

# ─────────────────────────────────────────
# Google Sheets
# ─────────────────────────────────────────
def connect_sheets():
    creds  = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet  = client.open_by_key(GOOGLE_SHEET_ID)
    ws     = sheet.sheet1

    if ws.row_values(1) == []:
        ws.update(range_name="A1", values=[["Timestamp", "Product", "Price", "Target", "Alert"]])

    return ws

# ─────────────────────────────────────────
# Selenium Price Scraper
# ─────────────────────────────────────────
def get_price(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--lang=en-US")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        driver.get("https://www.amazon.com")
        time.sleep(2)
        driver.add_cookie({"name": "i18n-prefs", "value": "USD"})
        driver.get(url)
        time.sleep(3)

        wait = WebDriverWait(driver, 10)

        selectors = [
            "#corePriceDisplay_desktop_feature_div span.a-price-whole",
            "#corePrice_desktop span.a-price-whole",
            "span.a-price-whole",
            "span.a-offscreen",
        ]

        for selector in selectors:
            try:
                el    = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                raw   = el.text.strip().replace(",", "")
                price = float(''.join(c for c in raw if c.isdigit() or c == '.'))
                if 100 < price < 10000:
                    return price
            except:
                continue

        print("  Could not find price on page.")
        return None

    except Exception as e:
        print(f"  Selenium error: {e}")
        return None

    finally:
        driver.quit()

# ─────────────────────────────────────────
# Telegram Alert
# ─────────────────────────────────────────
def send_alert(product, price):
    message = (
        f"Price Alert!\n\n"
        f"Product : {product['name']}\n"
        f"Price   : ${price}\n"
        f"Target  : ${product['target_price']}\n"
        f"Time    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"Buy it now before the price goes back up!"
    )

    url     = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}

    try:
        r = requests.post(url, data=payload)
        if r.json().get("ok"):
            print(f"  Alert sent via Telegram!")
    except Exception as e:
        print(f"  Telegram error: {e}")

# ─────────────────────────────────────────
# Log to Google Sheets
# ─────────────────────────────────────────
def log_to_sheets(ws, product, price, alerted):
    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        product["name"],
        price,
        product["target_price"],
        "YES" if alerted else "NO"
    ]
    ws.append_row(row)
    print(f"  Logged to Google Sheets.")

# ─────────────────────────────────────────
# Monitor Loop
# ─────────────────────────────────────────
def run_monitor():
    products = load_products()

    if not products:
        print("No products to monitor. Add one with --add first.")
        return

    print("=" * 50)
    print("Price Monitor Pro")
    print(f"Tracking {len(products)} product(s)")
    print(f"Checking every {CHECK_EVERY // 3600} hour(s)")
    print("=" * 50)

    ws      = connect_sheets()
    alerted = {p["name"]: False for p in products}

    try:
        while True:
            for product in products:
                name  = product["name"]
                print(f"\nChecking: {name}")

                price = get_price(product["url"])

                if price is None:
                    print(f"  Could not fetch price — skipping.")
                    continue

                print(f"  Current price: ${price}")
                print(f"  Target price : ${product['target_price']}")

                alert_sent = False

                if price < product["target_price"]:
                    if not alerted[name]:
                        send_alert(product, price)
                        alerted[name] = True
                        alert_sent    = True
                    else:
                        print(f"  Still below target — alert already sent.")
                else:
                    print(f"  Above target — no alert needed.")
                    alerted[name] = False

                log_to_sheets(ws, product, price, alert_sent)

            print(f"\nNext check in {CHECK_EVERY // 3600} hour(s)...")
            time.sleep(CHECK_EVERY)

    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("Price Monitor Pro stopped.")
        print("=" * 50)

# ─────────────────────────────────────────
# CLI
# ─────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Price Monitor Pro — Track Amazon prices from the command line."
    )

    subparsers = parser.add_subparsers(dest="command")

    # --add
    add_parser = subparsers.add_parser("add", help="Add a product to track")
    add_parser.add_argument("name",         type=str,   help="Product name")
    add_parser.add_argument("url",          type=str,   help="Amazon product URL")
    add_parser.add_argument("target_price", type=float, help="Target price in USD")

    # --remove
    remove_parser = subparsers.add_parser("remove", help="Remove a tracked product")
    remove_parser.add_argument("name", type=str, help="Product name to remove")

    # --list
    subparsers.add_parser("list", help="List all tracked products")

    # --run
    subparsers.add_parser("run", help="Start monitoring")

    args = parser.parse_args()

    if args.command == "add":
        add_product(args.name, args.url, args.target_price)
    elif args.command == "remove":
        remove_product(args.name)
    elif args.command == "list":
        list_products()
    elif args.command == "run":
        run_monitor()
    else:
        parser.print_help()

# ─────────────────────────────────────────
# Run
# ─────────────────────────────────────────
if __name__ == "__main__":
    main()