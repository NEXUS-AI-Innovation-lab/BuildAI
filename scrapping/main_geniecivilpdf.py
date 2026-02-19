import os
import re
import requests
from pathlib import Path
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from scrape_index_geniecivilpdf import scrape_index_pages
from scrape_article_geniecivilpdf import scrape_article

SCRIPT_DIR = Path(__file__).resolve().parent
RAW_DIR = SCRIPT_DIR / "raw_data"
os.makedirs(RAW_DIR, exist_ok=True)


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


def sanitize_filename(name: str) -> str:
    """Nettoie le nom de fichier pour éviter les caractères interdits"""
    return "".join(c if c.isalnum() or c in " ._-" else "_" for c in name)


def save_file(url, prefix=""):
    """Télécharge un fichier et le sauvegarde"""
    try:
        session = build_session()
        filename = url.split("/")[-1].split("?")[0]
        
        if not filename or len(filename) < 3:
            print(f"[SKIP] Nom invalide: {url}")
            return
        
        if prefix:
            filename = f"{prefix}_{filename}"
        
        filepath = RAW_DIR / sanitize_filename(filename)

        if filepath.exists():
            print(f"[SKIP] Déjà présent: {filename}")
            return

        r = session.get(url, stream=True, timeout=60)
        r.raise_for_status()
        
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        
        print(f"[SAVE] {filename}")
    except Exception as e:
        print(f"[ERROR] {url}: {e}")


def main():
    print("[INFO] Étape 1/3: Récupération de l'index...")
    urls = scrape_index_pages()
    print(f"\n[INFO] {len(urls)} pages trouvées\n")

    print("[INFO] Étape 2/3: Scraping de chaque article...\n")

    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url}")
        data = scrape_article(url)

        if not data["title"]:
            print("[SKIP] Pas de titre trouvé")
            continue

        prefix = sanitize_filename(data["title"])

        # HTML
        if data["content_html"]:
            html_path = RAW_DIR / f"{prefix}.html"
            try:
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(data["content_html"])
                print(f"[SAVE] HTML: {prefix}.html")
            except Exception as e:
                print(f"[ERROR] Sauvegarde HTML {prefix}: {e}")

        # PDFs
        print(f"[INFO] Téléchargement {len(data['pdf_urls'])} PDF(s)...")
        for pdf in data["pdf_urls"]:
            save_file(pdf, prefix)

        # Images
        print(f"[INFO] Téléchargement {len(data['image_urls'])} image(s)...")
        for img in data["image_urls"]:
            save_file(img, prefix)

        print()

    print("=" * 70)
    print("[SUCCESS] Scraping terminé!")
    print(f"[SUCCESS] Tous les fichiers sont dans: {RAW_DIR.resolve()}")
    print("=" * 70)


if __name__ == "__main__":
    main()
