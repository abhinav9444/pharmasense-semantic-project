import json
import time
import logging
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://togodb.org/entry/drugbank_lite/{}"
START_ID = 1
END_ID = 200
OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "scraped_drugbank_1_200.json"


def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    return session


def clean_value(cell):
    for br in cell.find_all("br"):
        br.replace_with("\n")
    value = cell.get_text(separator=" ", strip=True)
    return " ".join(value.split())


def scrape_drug(session, drug_id):
    url = BASE_URL.format(drug_id)
    try:
        response = session.get(url, timeout=30)
        if response.status_code != 200:
            logging.warning("ID %s returned HTTP %s", drug_id, response.status_code)
            return None

        soup = BeautifulSoup(response.text, "lxml")
        fields = {}
        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            key = cells[0].get_text(" ", strip=True)
            value = clean_value(cells[1])
            if key:
                fields[key] = value

        if not fields:
            logging.warning("No fields extracted for ID %s", drug_id)
            return None

        return {"source_id": drug_id, "source_url": url, "fields": fields}

    except requests.RequestException as exc:
        logging.error("Request failed for ID %s: %s", drug_id, exc)
        return None


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    session = create_session()
    drugs = []
    failed_ids = []

    for drug_id in range(START_ID, END_ID + 1):
        logging.info("Scraping ID %s/%s", drug_id, END_ID)
        drug = scrape_drug(session, drug_id)
        if drug:
            drugs.append(drug)
        else:
            failed_ids.append(drug_id)
        time.sleep(0.75)

    output = {
        "dataset": "DrugBank Lite",
        "source": "TogoDB",
        "base_url": BASE_URL,
        "requested_ids": END_ID - START_ID + 1,
        "successful_records": len(drugs),
        "failed_records": len(failed_ids),
        "failed_ids": failed_ids,
        "drugs": drugs,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)

    print(f"Scraped: {len(drugs)}/{END_ID - START_ID + 1}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
