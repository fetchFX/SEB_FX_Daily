
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
    listed = r.get("listed_currency", "")
    mid = r.get("exchange_rate", "")
    bid = r.get("bid_rate", "")
    offer = r.get("offer_rate", "")
    last_updated = r.get("last_updated_time", "")

    # Konvertera numeriska fält om möjligt
    def safe_float(v):
        try:
            return float(v) / 1000.0 if float(v) > 100 else float(v)
        except Exception:
            return ""

    rows.append({
        "retrieval_date": retrieval_date_utc,
        "listed_currency": listed,
        "exchange_rate": f"{safe_float(mid):.6f}" if mid else "",
        "bid_rate": f"{safe_float(bid):.6f}" if bid else "",
        "offer_rate": f"{safe_float(offer):.6f}" if offer else "",
        "last_updated_time": last_updated,
        "unit_currency": unit,
    })

# === Skriv CSV (skriv om filen varje gång) ===
csv_path = "fx_rates_sek.csv"

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "retrieval_date",
            "listed_currency",
            "exchange_rate",
            "bid_rate",
            "offer_rate",
            "last_updated_time",
            "unit_currency",
        ],
    )
    writer.writeheader()
    for row in rows:
        # säkerställ att alla kolumner finns
        for key in writer.fieldnames:
            if key not in row:
                row[key] = ""
        writer.writerow(row)

print(f"Wrote {len(rows)} rows to {csv_path} with new schema")
