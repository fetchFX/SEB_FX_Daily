from zoneinfo import ZoneInfo
from datetime import datetime
import csv
import requests
from bs4 import BeautifulSoup

URL = "https://seb.se/marknaden-och-kurslistor/valutakurser-avistakurser"
TARGET_COUNTRIES = {"Euro", "Storbritannien", "USA"}  # exakt som på sidan
TZ = ZoneInfo("Europe/Stockholm")

def clean_number(txt: str) -> float | None:
    if txt is None:
        return None
    # Ta bort vanliga och icke-brytande mellanslag + normalisera decimalpunkt
    t = txt.replace("\u00A0", "").replace(" ", "").replace("\t", "")
    t = t.replace(",", ".")
    # Tomt efter städning?
    if t == "" or t == "-":
        return None
    try:
        return float(t)
    except Exception:
        return None

def main():
    # Hämta HTML
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Hitta tabellen
    rows_out = []
    for tr in soup.select("table.table.text-nowrap.w-100 tr"):
        tds = tr.find_all("td")
        if len(tds) != 5:
            continue
        land = tds[0].get_text(strip=True)
        if land not in TARGET_COUNTRIES:
            continue

        valuta = tds[1].get_text(strip=True)
        kop_txt = tds[2].get_text(strip=True)
        salj_txt = tds[3].get_text(strip=True)
        datum = tds[4].get_text(strip=True)

        kop = clean_number(kop_txt)
        salj = clean_number(salj_txt)

        rows_out.append({
            "Land": land,
            "Valuta": valuta,
            "Köpkurs": kop,
            "Säljkurs": salj,
            "Datum": datum
        })

    # Bygg filnamn med Svensk tid (oavsett runnerns tidszon)
    now_se = datetime.now(TZ)
    yyyymmdd = now_se.strftime("%Y%m%d")
    filename = f"SEB_Avista_{yyyymmdd}.csv"

    # Skriv CSV (idempotent: skriv om samma fil om jobbet körs igen samma dag)
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Land", "Valuta", "Köpkurs", "Säljkurs", "Datum", "LoadDate"])
        for row in rows_out:
            w.writerow([
                row["Land"],
                row["Valuta"],
                row["Köpkurs"],
                row["Säljkurs"],
                row["Datum"],
                now_se.strftime("%Y-%m-%d %H:%M")
            ])

    print(f"Wrote {filename} with {len(rows_out)} rows.")

if __name__ == "__main__":
    main()
