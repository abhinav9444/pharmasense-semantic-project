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


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# ---------------------------------------------------------
# HTTP session with retry mechanism
# ---------------------------------------------------------

def create_session():
    session = requests.Session()

    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/151.0 Safari/537.36"
        )
    })

    return session


# ---------------------------------------------------------
# Convert HTML value into clean text
# ---------------------------------------------------------

def clean_value(cell):
    """
    Convert HTML inside a table cell into readable text.

    <br /> becomes a newline.
    HTML entities are automatically decoded by BeautifulSoup.
    """

    for br in cell.find_all("br"):
        br.replace_with("\n")

    value = cell.get_text(separator=" ", strip=True)

    # Normalize whitespace
    value = " ".join(value.split())

    return value


# ---------------------------------------------------------
# Parse one DrugBank Lite page
# ---------------------------------------------------------

def scrape_drug(session, drug_id):
    url = BASE_URL.format(drug_id)

    try:
        response = session.get(url, timeout=30)

        if response.status_code != 200:
            logging.warning(
                "ID %s returned HTTP %s",
                drug_id,
                response.status_code
            )
            return None

        soup = BeautifulSoup(response.text, "lxml")

        fields = {}

        # -------------------------------------------------
        # TogoDB displays the data as key/value table rows.
        # -------------------------------------------------

        rows = soup.find_all("tr")

        for row in rows:
            cells = row.find_all(["td", "th"])

            if len(cells) < 2:
                continue

            key = cells[0].get_text(" ", strip=True)
            value = clean_value(cells[1])

            if not key:
                continue

            # Store every field, including "-" and
            # "Not Available", because the assignment asks
            # for all source data.
            fields[key] = value

        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if not fields:
            logging.warning(
                "No fields extracted for ID %s",
                drug_id
            )
            return None

        return {
            "source_id": drug_id,
            "source_url": url,
            "fields": fields
        }

    except requests.RequestException as exc:
        logging.error(
            "Request failed for ID %s: %s",
            drug_id,
            exc
        )
        return None

    except Exception as exc:
        logging.exception(
            "Parsing failed for ID %s: %s",
            drug_id,
            exc
        )
        return None


# ---------------------------------------------------------
# Main scraper
# ---------------------------------------------------------

def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    session = create_session()

    drugs = []
    failed_ids = []

    total = END_ID - START_ID + 1

    logging.info(
        "Starting scrape of %s DrugBank Lite IDs",
        total
    )

    for drug_id in range(START_ID, END_ID + 1):

        logging.info(
            "Scraping ID %s/%s",
            drug_id,
            END_ID
        )

        drug = scrape_drug(session, drug_id)

        if drug is not None:
            drugs.append(drug)
        else:
            failed_ids.append(drug_id)

        # Be polite to the server.
        time.sleep(0.75)

    # -----------------------------------------------------
    # Final structured dataset
    # -----------------------------------------------------

    output = {
        "dataset": "DrugBank Lite",
        "source": "TogoDB",
        "base_url": "https://togodb.org/entry/drugbank_lite/{id}",
        "requested_ids": total,
        "successful_records": len(drugs),
        "failed_records": len(failed_ids),
        "failed_ids": failed_ids,
        "drugs": drugs
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False
        )

    logging.info("=" * 60)
    logging.info(
        "Scraping completed: %s/%s records",
        len(drugs),
        total
    )
    logging.info(
        "Failed IDs: %s",
        failed_ids
    )
    logging.info(
        "Output: %s",
        OUTPUT_FILE
    )


if __name__ == "__main__":
    main()