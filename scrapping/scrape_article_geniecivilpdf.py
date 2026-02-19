import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


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


def extract_files(article_url, soup):
    """Extrait les PDFs et images avec détection robuste"""
    pdf_links = []
    for a in soup.select("a[href]"):
        href = a["href"].strip().lower()
        text = a.get_text(" ", strip=True).lower()

        if any(x in href for x in ["pdf", "drive.google", "mediafire", "mega.nz"]) \
           or any(x in text for x in ["pdf", "télécharger", "telecharger", "download"]):
            pdf_links.append(urljoin(article_url, a["href"]))

    img_links = []
    for img in soup.select("img[src]"):
        src = img["src"]
        if any(ext in src.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
            img_links.append(urljoin(article_url, src))

    return list(set(pdf_links)), list(set(img_links))


def extract_clean_html(soup):
    """Extrait le contenu HTML nettoyé avec fallback"""
    content = soup.find("div", class_="entry-content") or soup.find("article")
    
    if not content:
        return ""

    for tag in content(["script", "style", "iframe", "noscript"]):
        tag.decompose()

    return str(content)


def scrape_article(url):
    session = build_session()
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"✖ erreur scrape {url}: {e}")
        return {
            "title": "",
            "content_html": "",
            "pdf_urls": [],
            "image_urls": []
        }

    soup = BeautifulSoup(r.text, "html.parser")

    title = soup.find("h1")
    title = title.get_text(strip=True) if title else url.split("/")[-1]

    # Extraction HTML
    content_html = extract_clean_html(soup)

    # Extraction PDFs et images
    pdf_urls, image_urls = extract_files(url, soup)

    return {
        "title": title,
        "content_html": content_html,
        "pdf_urls": pdf_urls,
        "image_urls": image_urls
    }

