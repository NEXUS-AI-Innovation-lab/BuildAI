import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://geniecivilpdf.com"
INDEX_URL = "https://geniecivilpdf.com/pdf/"


def build_session():
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def scrape_index_pages():
    session = build_session()
    try:
        r = session.get(INDEX_URL, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"✖ erreur index {INDEX_URL}: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    article_urls = set()

    for a in soup.select("a[href]"):
        href = a.get("href")
        if not href:
            continue

        full_url = urljoin(BASE_URL, href)

        # On garde les articles mais on exclut les filtres et PDFs
        if (
            full_url.startswith(BASE_URL)
            and "?" not in full_url
            and not full_url.lower().endswith(".pdf")
            and full_url != INDEX_URL.rstrip("/")
            and full_url != BASE_URL
        ):
            article_urls.add(full_url)

    return list(article_urls)
