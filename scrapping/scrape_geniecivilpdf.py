import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin
import re
import time
import os

# Save output next to this script by default (scrapping/raw_data).
# Can be overridden with the RAW_DATA_PATH environment variable.
SCRIPT_DIR = Path(__file__).resolve().parent
RAW_DIR = Path(os.getenv("RAW_DATA_PATH", SCRIPT_DIR / "raw_data"))
RAW_DIR.mkdir(parents=True, exist_ok=True)

INDEX_URL = "https://geniecivilpdf.com/pdf/"
BASE_URL = "https://geniecivilpdf.com"


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


SESSION = build_session()


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def get_article_links():
    try:
        r = SESSION.get(INDEX_URL, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"✖ erreur index {INDEX_URL}: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    links = set()
    for a in soup.select("a[href]"):
        href = a.get("href")
        if not href:
            continue

        href = href.strip()
        if href.startswith("#"):
            continue

        full_url = urljoin(BASE_URL, href)

        if full_url.startswith(BASE_URL) and "/pdf/" not in full_url:
            links.add(full_url)

    return list(links)


def extract_files(article_url):
    r = SESSION.get(article_url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    pdf_links = []
    for a in soup.select("a[href]"):
        href = a["href"]
        if ".pdf" in href.lower():
            pdf_links.append(urljoin(INDEX_URL, href))

    img_links = []
    for img in soup.select("img[src]"):
        src = img["src"]
        if any(ext in src.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
            img_links.append(urljoin(INDEX_URL, src))

    return pdf_links, img_links, soup


def extract_clean_html(soup):
    content = soup.find("div", class_="entry-content")
    if not content:
        return "", ""

    for tag in content(["script", "style", "iframe", "noscript"]):
        tag.decompose()

    clean_html = str(content)
    clean_text = content.get_text(separator="\n", strip=True)
    return clean_html, clean_text


def save_remote_file(url, dest: Path):
    try:
        r = SESSION.get(url, timeout=60)
        r.raise_for_status()
        dest.write_bytes(r.content)
        return True
    except Exception as e:
        print(f"✖ téléchargement échoué {url}: {e}")
        return False


def scrape_article(url):
    try:
        pdf_links, img_links, soup = extract_files(url)

        title_tag = soup.select_one("h1")
        title = title_tag.get_text(strip=True) if title_tag else url.split("/")[-1]
        slug = slugify(title)

        # Clean HTML saved as .html + plain text as .txt for RAG ingestion
        clean_html, clean_text = extract_clean_html(soup)

        html_path = RAW_DIR / f"{slug}.html"
        if clean_html:
            html_path.write_text(clean_html, encoding="utf-8")

        txt_path = RAW_DIR / f"{slug}.txt"
        if clean_text:
            txt_path.write_text(clean_text, encoding="utf-8")

        # Save PDFs
        for i, pdf in enumerate(pdf_links):
            pdf_name = RAW_DIR / f"{slug}.pdf" if i == 0 else RAW_DIR / f"{slug}_{i+1}.pdf"
            if not pdf_name.exists():
                save_remote_file(pdf, pdf_name)

        # Save images (jpg/png)
        for i, img in enumerate(img_links):
            ext = Path(img).suffix or ".jpg"
            img_name = RAW_DIR / f"{slug}_{i+1}{ext}"
            if not img_name.exists():
                save_remote_file(img, img_name)

        print(f"✔ {slug}")
    except Exception as e:
        print(f"✖ erreur sur {url}: {e}")


def main():
    urls = get_article_links()
    print(f"{len(urls)} articles trouvés")

    for url in urls:
        scrape_article(url)
        time.sleep(0.8)


if __name__ == "__main__":
    main()
