import csv
import os

BASE_URL = "https://bidplus.gem.gov.in"

HEADERS = [
    "serial_no",
    "bid_no",
    "bid_url",
    "ra_no",
    "ra_url",
    "status",
    "bid_result_url",   # View Bid Results
    "ra_result_url"     # View RA Results (NEW)
]


def init_csv(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(HEADERS)


def extract_current_page(
    page,
    csv_path,
    start_serial,
    browser_context,   # kept for compatibility
    result_csv_path    # kept for compatibility
):
    """
    Extract listing page data ONLY.
    If 'View Bid Results' or 'View RA Results' buttons exist,
    capture their URLs without clicking.
    """

    page.wait_for_timeout(1500)

    cards = page.locator("div.card")
    total = cards.count()

    serial = start_serial

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        for i in range(total):
            card = cards.nth(i)

            bid_no = ""
            bid_url = ""
            ra_no = ""
            ra_url = ""
            status = ""
            bid_result_url = ""
            ra_result_url = ""

            # --- BID / RA DETAILS ---
            labels = card.locator("span.bid_title")
            for j in range(labels.count()):
                label = labels.nth(j)
                text = label.inner_text().upper()

                anchor = label.locator("xpath=following-sibling::a").first
                if anchor.count() == 0:
                    continue

                value = anchor.inner_text().strip()
                href = anchor.get_attribute("href")

                if "BID NO" in text:
                    bid_no = value
                    bid_url = BASE_URL + href if href else ""

                elif "RA NO" in text:
                    ra_no = value
                    ra_url = BASE_URL + href if href else ""

            # --- STATUS ---
            full_text = card.inner_text()
            if "Status:" in full_text:
                status = (
                    full_text.split("Status:")[1]
                    .split("\n")[0]
                    .strip()
                )

            # --- VIEW BID RESULT URL (NO CLICK) ---
            # User reported 'View BID Results' (uppercase BID)
            bid_result_anchor = card.locator(
                "a:has(input[value='View BID Results'])"
            )
            if bid_result_anchor.count() == 0:
                # Fallback to 'View Bid Results' just in case
                bid_result_anchor = card.locator(
                    "a:has(input[value='View Bid Results'])"
                )

            if bid_result_anchor.count() > 0:
                href = bid_result_anchor.first.get_attribute("href")
                if href:
                    bid_result_url = BASE_URL + href
                    print("   ↳ Bid Result URL captured")

            # --- VIEW RA RESULT URL (NO CLICK) ---
            ra_result_anchor = card.locator(
                "a:has(input[value='View RA Results'])"
            )
            if ra_result_anchor.count() > 0:
                href = ra_result_anchor.first.get_attribute("href")
                if href:
                    ra_result_url = BASE_URL + href
                    print("   ↳ RA Result URL captured")

            # --- SAVE ROW ---
            writer.writerow([
                serial,
                bid_no,
                bid_url,
                ra_no,
                ra_url,
                status,
                bid_result_url,
                ra_result_url
            ])

            print(f"[ROW {serial}] Extracted")
            serial += 1

    return serial
