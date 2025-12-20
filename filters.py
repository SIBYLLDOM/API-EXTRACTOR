def apply_filters(page):
    # wait for filters panel to load
    page.wait_for_selector("text=Filters", timeout=15000)

    # Ongoing Bids/RA
    ongoing_label = page.locator("label:has-text('Ongoing Bids/RA')")

    # Bid/RA Status
    bid_ra_label = page.locator("label:has-text('Bid/RA Status')")

    # turn OFF Ongoing Bids/RA if checked
    if "checked" in ongoing_label.inner_html():
        ongoing_label.click()
        page.wait_for_timeout(1500)

    # turn ON Bid/RA Status if not checked
    if "checked" not in bid_ra_label.inner_html():
        bid_ra_label.click()
        page.wait_for_timeout(3000)

    # wait for results refresh
    page.wait_for_timeout(4000)
