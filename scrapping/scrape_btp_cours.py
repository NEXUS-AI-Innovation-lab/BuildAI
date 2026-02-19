import os
import requests
import warnings
from urllib.parse import urljoin
from urllib3.exceptions import NotOpenSSLWarning
from bs4 import BeautifulSoup
from scraper_category import scrape_category_pages
from scrape_article import scrape_article

# -----------------------------
# Ignorer le warning LibreSSL
# -----------------------------
warnings.simplefilter("ignore", NotOpenSSLWarning)

# -----------------------------
# Dossier de stockage unique
# -----------------------------
RAW_DIR = "scrapping/raw_data"
os.makedirs(RAW_DIR, exist_ok=True)

# -----------------------------
# Fonctions utilitaires
# -----------------------------
def sanitize_filename(name: str) -> str:
    """Nettoie le nom de fichier pour éviter les caractères interdits"""
    return "".join(c if c.isalnum() or c in " ._-" else "_" for c in name)

def save_html(title: str, html: str):
    """Sauvegarde le HTML d'un article"""
    filename = sanitize_filename(f"{title}.html")
    filepath = os.path.join(RAW_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[SAVE] HTML : {filepath}")

def download_file(url: str):
    """Télécharge PDF ou image depuis une URL"""
    if not url:
        return
    
    # Nettoie l'URL
    url = url.split('?')[0]  # Retire les paramètres
    filename = sanitize_filename(url.split("/")[-1])
    
    if not filename or len(filename) < 3:
        print(f"[SKIP] Nom de fichier invalide pour {url}")
        return
        
    filepath = os.path.join(RAW_DIR, filename)

    if os.path.exists(filepath):
        print(f"[SKIP] Déjà présent: {filename}")
        return

    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        print(f"[SAVE] Téléchargé: {filename}")
    except Exception as e:
        print(f"[ERROR] Échec {url}: {e}")

# -----------------------------
# Script principal
# -----------------------------
def main():
    print("[INFO] Étape 1/3: Récupération de toutes les URLs d'articles...")
    article_urls = scrape_category_pages()  # Scrape TOUTES les pages (pas de limite)
    print(f"\n[INFO] {len(article_urls)} articles trouvés au total\n")

    print("[INFO] Étape 2/3: Scraping de chaque article...")
    
    for idx, url in enumerate(article_urls, 1):
        print(f"\n[{idx}/{len(article_urls)}] Traitement: {url}")
        data = scrape_article(url)

        if not data["content_html"]:
            print("[SKIP] Pas de contenu HTML trouvé")
            continue

        # 1️⃣ Sauvegarde du HTML
        save_html(data["title"], data["content_html"])

        # 2️⃣ Téléchargement des PDFs
        for pdf_url in data["pdf_urls"]:
            full_pdf_url = urljoin(url, pdf_url)
            download_file(full_pdf_url)

        # 3️⃣ Téléchargement des images
        soup = BeautifulSoup(data["content_html"], "html.parser")
        for img in soup.find_all("img", src=True):
            img_url = urljoin(url, img["src"])
            download_file(img_url)

    print("\n" + "="*70)
    print("[SUCCESS] Scraping terminé!")
    print(f"[SUCCESS] Tous les fichiers sont dans: {os.path.abspath(RAW_DIR)}")
    print("="*70)

# -----------------------------
if __name__ == "__main__":
    main()
