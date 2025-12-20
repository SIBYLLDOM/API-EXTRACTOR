from fastapi import FastAPI, Query, HTTPException
import requests
from bs4 import BeautifulSoup

app = FastAPI(title="GeM Bid Scraper API")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html"
}

TECHNICAL_KEYWORDS = ["seller", "offered", "participated", "mse", "status"]
FINANCIAL_KEYWORDS = ["seller", "offered", "price", "rank"]


def norm(text: str) -> str:
    return text.lower().replace("\xa0", " ").replace("\n", " ").strip()


def fetch_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def extract_basic_info(soup):
    data = {"bid_info": {}, "buyer_details": {}}
    for p in soup.select("div.block p"):
        strong, span = p.find("strong"), p.find("span")
        if strong and span:
            key = norm(strong.text).replace(":", "")
            data["bid_info"][key] = span.text.strip()
    return data


def extract_rows(table):
    return [[td.get_text(" ", strip=True) for td in tr.find_all("td")]
            for tr in table.find_all("tr")[1:]]


def extract_tables(soup):
    technical = financial = None

    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if not headers:
            continue

        header_text = " ".join(norm(h) for h in headers)

        if not technical and all(k in header_text for k in TECHNICAL_KEYWORDS):
            technical = {"headers": headers, "rows": extract_rows(table)}

        if not financial and all(k in header_text for k in FINANCIAL_KEYWORDS):
            financial = {"headers": headers + ["Winner"], "rows": extract_rows(table)}

    return technical, financial


@app.get("/scrap")
def scrap(url: str = Query(...)):
    try:
        html = fetch_html(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    soup = BeautifulSoup(html, "html.parser")
    basic = extract_basic_info(soup)
    tech, fin = extract_tables(soup)

    return {
        "basic_info": basic,
        "technical_evaluation": tech,
        "financial_evaluation": fin
    }
