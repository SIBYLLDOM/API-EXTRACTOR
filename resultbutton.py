import csv
import os
import requests

API_BASE = "http://localhost:8000/scrap?url="

INPUT_CSV = "output/main_rowdata.csv"
OUTPUT_DIR = "output"

BID_INFO_CSV = os.path.join(OUTPUT_DIR, "bid_info.csv")
TECH_CSV = os.path.join(OUTPUT_DIR, "technical.csv")
FIN_CSV = os.path.join(OUTPUT_DIR, "financial.csv")


def append_dict_to_csv(data: dict, path: str):
    if not data:
        return

    file_exists = os.path.exists(path)

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)


def append_table_to_csv(headers, rows, path, extra_meta=None):
    if not headers or not rows:
        return

    headers = list(headers)

    if extra_meta:
        headers = list(extra_meta.keys()) + headers

    file_exists = os.path.exists(path)

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(headers)

        for row in rows:
            if extra_meta:
                writer.writerow(list(extra_meta.values()) + row)
            else:
                writer.writerow(row)


def process_results():
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            bid_no = row.get("bid_no", "").strip()
            result_url = row.get("bid_result_url", "").strip()

            if not result_url:
                continue

            print(f"📡 Fetching result → {bid_no}")

            try:
                r = requests.get(API_BASE + result_url, timeout=60)
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                print(f"❌ API failed for {bid_no}: {e}")
                continue

            # ---------- BID INFO ----------
            bid_info = data.get("basic_info", {}).get("bid_info")
            if bid_info:
                bid_info["bid_no"] = bid_no
                append_dict_to_csv(bid_info, BID_INFO_CSV)

            # ---------- TECHNICAL ----------
            tech = data.get("technical_evaluation")
            if tech:
                append_table_to_csv(
                    tech.get("headers"),
                    tech.get("rows"),
                    TECH_CSV,
                    extra_meta={"bid_no": bid_no}
                )

            # ---------- FINANCIAL ----------
            fin = data.get("financial_evaluation")
            if fin:
                append_table_to_csv(
                    fin.get("headers"),
                    fin.get("rows"),
                    FIN_CSV,
                    extra_meta={"bid_no": bid_no}
                )

            print(f"✅ Appended → {bid_no}")


if __name__ == "__main__":
    process_results()
