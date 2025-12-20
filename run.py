import os
import time
from browser import get_browser
from filters import apply_filters
from extractor import init_csv, extract_current_page
from resultbutton import process_results

# ---------------- CONFIG ----------------
SITE_URL = "https://bidplus.gem.gov.in/all-bids"
OUTPUT_DIR = "output"
CSV_FILE = os.path.join(OUTPUT_DIR, "main_rowdata.csv")
TOTAL_PAGES = 10


# ---------------- HELPERS ----------------
def scroll_to_top(page):
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)


def wait_for_cards_soft(page, max_wait=20):
    start = time.time()
    while time.time() - start < max_wait:
        try:
            if page.locator("div.card").count() > 0:
                return True
        except:
            pass
        page.wait_for_timeout(500)
    return False


# ---------------- MAIN ----------------
def run():
    print("\n🟡 PHASE-1: Listing Extraction Started")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    playwright, browser, page = get_browser()
    context = page.context

    page.goto(SITE_URL, timeout=60000)
    page.wait_for_load_state("networkidle")

    apply_filters(page)
    page.wait_for_load_state("networkidle")

    init_csv(CSV_FILE)

    serial_no = 1

    for page_no in range(1, TOTAL_PAGES + 1):
        print(f"\n========== PAGE {page_no} ==========")

        scroll_to_top(page)
        wait_for_cards_soft(page)

        serial_no = extract_current_page(
            page=page,
            csv_path=CSV_FILE,
            start_serial=serial_no,
            browser_context=context,
            result_csv_path=None
        )

        # move to next page using page-number click
        if page_no < TOTAL_PAGES:
            next_page = page_no + 1
            print(f"➡️ Moving to page {next_page}")

            page.evaluate(
                f"""() => {{
                    const link = document.querySelector(
                        "a.page-link[href='#page-{next_page}']"
                    );
                    if (link) link.click();
                }}"""
            )

            page.wait_for_timeout(2500)

    print("\n🟢 PHASE-1 Completed — main_rowdata.csv ready")

    print("\n🛑 Closing browser...")
    browser.close()
    playwright.stop()

    # ---------------- PHASE 2 ----------------
    print("\n🟡 PHASE-2: Result Button API Extraction Started")
    process_results()

    print("\n✅ ALL PHASES COMPLETED SUCCESSFULLY\n")


if __name__ == "__main__":
    run()
