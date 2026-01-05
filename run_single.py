import os
import time
import sys
import csv
from bs4 import BeautifulSoup

# Add api folder to path to import api logic
sys.path.append(os.path.join(os.getcwd(), 'api'))
from api import fetch_html, extract_basic_info, extract_tables

from browser import get_browser
from filters import apply_filters
from extractor import init_csv, extract_current_page

# ---------------- CONFIG ----------------
SITE_URL = "https://bidplus.gem.gov.in/all-bids"
OUTPUT_DIR = "output"
CSV_FILE = os.path.join(OUTPUT_DIR, "single_bid_data.csv")

# Result CSV Config
BASIC_CSV = os.path.join(OUTPUT_DIR, "single_bid_results_basic.csv")
TECH_CSV = os.path.join(OUTPUT_DIR, "single_bid_results_technical.csv")
FIN_CSV = os.path.join(OUTPUT_DIR, "single_bid_results_financial.csv")

def save_dict_to_csv(data_dict, path):
    """Saves a dictionary as a single row CSV (keys as headers)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file_exists = os.path.exists(path)
    
    with open(path, "w", newline="", encoding="utf-8") as f: # Overwrite for single run mode
        writer = csv.DictWriter(f, fieldnames=data_dict.keys())
        writer.writeheader()
        writer.writerow(data_dict)
    print(f"   ↳ Saved {path}")

def save_table_to_csv(headers, rows, path):
    """Saves table data (list of lists) to CSV."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, "w", newline="", encoding="utf-8") as f: # Overwrite
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"   ↳ Saved {path}")

def process_bid_result(url):
    """
    Fetches the bid result page and extracts details using api.py logic.
    Saves to 3 separate CSVs.
    """
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Basic Info
    basic_data = extract_basic_info(soup)
    if basic_data and "bid_info" in basic_data:
        # Flatten bid_info and buyer_details if needed, but api returns them nested.
        # Let's combine them for the CSV
        flat_data = {**basic_data.get("bid_info", {}), **basic_data.get("buyer_details", {})}
        if flat_data:
            save_dict_to_csv(flat_data, BASIC_CSV)
    
    # 2. Tables (Technical / Financial)
    tech, fin = extract_tables(soup)
    
    if tech:
        save_table_to_csv(tech["headers"], tech["rows"], TECH_CSV)
    
    if fin:
        save_table_to_csv(fin["headers"], fin["rows"], FIN_CSV)


def search_bid(page, bid_number):
    """
    Inputs the bid number into the search bar and triggers the search.
    """
    print(f"\n🔍 Searching for Bid Number: {bid_number}")
    
    # Wait for the search bar to be visible
    search_input = page.locator("#searchBid")
    search_input.wait_for(state="visible", timeout=10000)
    
    # Clear and fill the search bar
    search_input.fill("")
    search_input.fill(bid_number)
    
    # Trigger search (usually by pressing Enter or waiting if it's auto-search, 
    # but based on standard forms, Enter is safe).
    # The user request mentioned "IN THE SEARCH BAR ... I NEED TO SEARCH"
    search_input.press("Enter")
    
    # Wait for the table/results to refresh. 
    # We can wait for the network idle or a specific element change.
    page.wait_for_load_state("networkidle")
    time.sleep(3) # safe buffer for JS framwork to re-render

def run_single():
    print("\n🟡 PHASE-1: Single Bid Extraction Started")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    playwright, browser, page = get_browser()
    context = page.context

    try:
        page.goto(SITE_URL, timeout=60000)
        page.wait_for_load_state("networkidle")

        # Apply the same filters as the main run
        apply_filters(page)
        page.wait_for_load_state("networkidle")

        # Initialize the single bid CSV (overwrite or append? Let's overwrite for a "single run" to be clean, 
        # or valid append. The user said "run_single", implying a specific task. 
        # I'll append so history is kept, but init_csv handles header creation if missing.)
        init_csv(CSV_FILE)

        while True:
            # Get Bid Number from User
            bid_number = input("\n⌨️ Enter Bid Number to search (or 'q' to quit): ").strip()
            
            if bid_number.lower() == 'q':
                break
                
            if not bid_number:
                print("⚠️ Please enter a valid Bid Number.")
                continue

            # Search for the bid
            search_bid(page, bid_number)

            # Check if any results appeared
            if page.locator("div.card").count() == 0:
                print("❌ No results found for this Bid Number.")
                continue

            # Extract data
            serial = extract_current_page(
                page=page,
                csv_path=CSV_FILE,
                start_serial=1, # Always 1 for single entry or we could track it.
                browser_context=context,
                result_csv_path=None
            )
            print(f"✅ Data saved to {CSV_FILE}")

            # --- NEW: DEEP EXTRACTION USING API LOGIC ---
            # Read the file to get the URL we just saved
            last_row = None
            if os.path.exists(CSV_FILE):
                with open(CSV_FILE, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    if rows:
                        last_row = rows[-1]
            
            if last_row and last_row.get("bid_result_url"):
                result_url = last_row["bid_result_url"]
                print(f"\n🔍 Extracting details from: {result_url}")
                try:
                    process_bid_result(result_url)
                except Exception as e:
                     print(f"❌ Failed to extract detailed results: {e}")
            else:
                print("⚠️ No Bid Result URL found to extract details for.")
            
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
    finally:
        print("\n🛑 Closing browser...")
        browser.close()
        playwright.stop()

if __name__ == "__main__":
    run_single()
