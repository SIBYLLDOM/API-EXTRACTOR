import csv
import os
import requests
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Lock
from urllib.parse import quote


# ---------------- CONFIG ----------------
API_BASE = "http://localhost:8000/scrap?url="
INPUT_CSV = "output/main_rowdata.csv"
OUTPUT_DIR = "output"

BID_INFO_CSV = os.path.join(OUTPUT_DIR, "bid_info.csv")
TECH_CSV = os.path.join(OUTPUT_DIR, "technical.csv")
FIN_CSV = os.path.join(OUTPUT_DIR, "financial.csv")

WORKERS = 10
CSV_LOCK = Lock()


# ---------------- CSV HELPERS ----------------
def append_dict(data: dict, path: str):
    """
    Writes dict data to CSV with headers written once.
    """
    if not data:
        return

    file_exists = os.path.exists(path)

    with CSV_LOCK:
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data.keys())

            if not file_exists:
                writer.writeheader()

            writer.writerow(data)


def append_table(headers, rows, path, bid_no):
    """
    Writes table data with correct column headers.
    """
    if not headers or not rows:
        return

    full_headers = ["bid_no"] + headers
    file_exists = os.path.exists(path)

    with CSV_LOCK:
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            if not file_exists:
                writer.writerow(full_headers)

            for row in rows:
                writer.writerow([bid_no] + row)


# ---------------- WORKER ----------------
def process_single_bid(task):
    bid_no, result_url = task

    if "getBidResultView/" not in result_url:
        print(f"⏭️ Skipped non-result URL for {bid_no}")
        return

    try:
        encoded_url = quote(result_url, safe="")
        r = requests.get(API_BASE + encoded_url, timeout=60)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"❌ API error for {bid_no}: {e}")
        return

    # ---------- BID INFO ----------
    bid_info = data.get("basic_info", {}).get("bid_info")
    if bid_info:
        bid_info["bid_no"] = bid_no
        append_dict(bid_info, BID_INFO_CSV)

    # ---------- TECHNICAL ----------
    tech = data.get("technical_evaluation")
    if tech and tech.get("headers") and tech.get("rows"):
        append_table(
            tech["headers"],
            tech["rows"],
            TECH_CSV,
            bid_no
        )

    # ---------- FINANCIAL ----------
    fin = data.get("financial_evaluation")
    if fin and fin.get("headers") and fin.get("rows"):
        append_table(
            fin["headers"],
            fin["rows"],
            FIN_CSV,
            bid_no
        )

    print(f"✅ Completed {bid_no}")


# ---------------- MAIN ----------------
def process_results():
    tasks = []

    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bid_no = row.get("bid_no", "").strip()
            result_url = row.get("bid_result_url", "").strip()
            if bid_no and result_url:
                tasks.append((bid_no, result_url))

    print(f"\n🚀 Dispatching {len(tasks)} bids to {WORKERS} workers\n")

    with ProcessPoolExecutor(max_workers=WORKERS) as executor:
        executor.map(process_single_bid, tasks)
