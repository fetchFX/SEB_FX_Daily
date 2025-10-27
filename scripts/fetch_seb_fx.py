
import os, json, csv, datetime, zoneinfo
import urllib.request

# === Hämta API-nyckeln från GitHub Secret ===
API_KEY = os.environ["SEB_API_KEY"]

# === API-url (production) ===
BASE = "https://api.sebgroup.com/open/prod/fxrates/v3/fx-spot-exchange-rate?unit_currency=SEK"

# === Hämta data ===
req = urllib.request.Request(
    BASE,
    headers={
        "X-IBM-Client-Id": API_KEY,
        "Accept": "application/json"
    }
)
with urllib.request.urlopen(req, timeout=20) as resp:
    data = json.loads(resp.read().decode("utf-8"))

# === Extrahera basinformation ===
unit = data["unit_currency"]
spot_list = data["fx_spot_exchange_rates"]
if not spot_list:
    raise RuntimeError("No fx_spot_exchange_rates in response")

retrieval_date_utc = spot_list[0]["retrieval_date"]  # Ex: 2025-10-15T15:00:00Z

rows = []
for r in spot_list[0]["fx_spot_mid_exchange_rates"]:
    listed = r["listed_currency"]
    ex = r["exchange_rate"]

    # SEB skickar ibland tal *1000 -> dela vid behov
    ex = float(ex) / 1000.0

    last_updated_utc = r["last_updated_time"]  # ISO 8601 UTC

    # Konvertera UTC -> svensk tid
    dt_utc = datetime.datetime.fromisoformat(last_updated_utc.replace("Z", "+00:00"))
    dt_se = dt_utc.astimezone(zoneinfo.ZoneInfo("Europe/Stockholm"))

    rows.append({
        "retrieval_date": retrieval_date_utc,
        "listed_currency": listed,
        "exchange_rate": f"{ex:.6f}",
        "unit_currency": unit,
        "last_updated_time_utc": last_updated_utc,
        "last_updated_time_se": dt_se.strftime("%Y-%m-%d %H:%M:%S")
    })

# === Skriv/uppdatera CSV ===
csv_path = "fx_rates_sek.csv"
file_exists = os.path.exists(csv_path)

with open(csv_path, "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "retrieval_date",
            "listed_currency",
            "exchange_rate",
            "unit_currency",
            "last_updated_time_utc",
            "last_updated_time_se",
        ],
    )
    if not file_exists:
        writer.writeheader()
    for row in rows:
        writer.writerow(row)

print(f"Wrote {len(rows)} rows to {csv_path}")
  
