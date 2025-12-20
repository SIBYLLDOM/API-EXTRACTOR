from playwright.sync_api import sync_playwright

def get_browser():
    playwright = sync_playwright().start()

    browser = playwright.chromium.launch(
        headless=False,        # 🔥 HUGE SPEED BOOST
        args=[
            "--disable-images",
            "--disable-extensions",
            "--disable-gpu",
            "--no-sandbox"
        ]
    )

    context = browser.new_context(
        viewport={"width": 1280, "height": 800}
    )

    page = context.new_page()
    return playwright, browser, page
