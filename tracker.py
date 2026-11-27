import csv
import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

urls = [
    "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
    "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html",
    "https://books.toscrape.com/catalogue/soumission_998/index.html",
]

CSV_FILE = "prices.csv"
WEBHOOK = os.environ.get("DISCORD_WEBHOOK")


def get_last_prices():
    """Return {url: most recent saved price} from the CSV."""
    last = {}
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                last[row["url"]] = float(row["price"])  # later rows overwrite earlier ones
    return last


def send_alert(message):
    if not WEBHOOK:
        print("No webhook set, alert would be:", message)
        return
    requests.post(WEBHOOK, json={"content": message}, timeout=10)


last_prices = get_last_prices()  # read BEFORE we append new rows
file_exists = os.path.exists(CSV_FILE)

with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(["timestamp", "product", "price", "url"])

    for url in urls:
        response = requests.get(url, timeout=10)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.find("h1").text
        price_text = soup.find("p", class_="price_color").text
        price = float(re.sub(r"[^\d.]", "", price_text))

        old_price = last_prices.get(url)
        if old_price is not None and price < old_price:
            send_alert(f"Price drop, <@726568795992358973>! {title}: {old_price} -> {price}\n{url}")

        writer.writerow([datetime.now().isoformat(timespec="seconds"), title, price, url])
        print(f"Saved: {title} - {price}")