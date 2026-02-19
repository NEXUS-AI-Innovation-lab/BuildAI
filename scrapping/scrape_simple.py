"""
Scraping simple et robuste - GARANTI DE FONCTIONNER
Utilise requests + BeautifulSoup (méthode classique)
"""

from pathlib import Path
import requests
import re
import logging
import os
from bs4 import BeautifulSoup
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
RAW_DIR = Path(os.getenv("RAW_DATA_PATH", "storage/raw_data"))
RAW_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://www.btp-cours.com/category/documents/document-pdf"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def slugify(text: str) -> str:
    """Convertit un titre en nom de fichier sécurisé"""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:100]  # Limite à 100 caractères


def download_pdf(url: str, filename: str) -> bool:
    """Télécharge un PDF avec gestion d'erreurs"""
    try:
        logger.info(f"    Téléchargement de {url[:60]}...")
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        filepath = RAW_DIR / filename
        filepath.write_bytes(response.content)
        logger.info(f"    ✔ Sauvegardé: {filename}")
        return True
    except Exception as e:
        logger.error(f"    ✗ Erreur: {e}")
        return False


def scrape_btp_cours(limit: int = 5):
    """
    Scrape simple et efficace
    """
    logger.info(f"{'='*70}")
    logger.info(f"🚀 Démarrage du scraping: {BASE_URL}")
    logger.info(f"{'='*70}\n")
    
    try:
        # 1. Récupère la page d'index
        logger.info("📄 Récupération de la page d'index...")
        response = requests.get(BASE_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        logger.info(f"✓ Page récupérée ({len(response.text)} caractères)")
        
        # 2. Parse avec BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('article')
        
        logger.info(f"✓ {len(articles)} articles trouvés\n")
        
        if not articles:
            logger.warning("⚠️ Aucun article trouvé! Le HTML a peut-être changé.")
            return
        
        # 3. Traite chaque article
        count = 0
        for idx, art in enumerate(articles[:limit], 1):
            try:
                logger.info(f"[{idx}/{limit}] Traitement de l'article...")
                
                # Trouve le titre et lien
                title_el = art.find('h2')
                if not title_el:
                    logger.warning("  ⊘ Pas de <h2> trouvé")
                    continue
                
                link_el = title_el.find('a')
                if not link_el:
                    logger.warning("  ⊘ Pas de lien trouvé")
                    continue
                
                article_url = link_el.get('href')
                title = link_el.get_text(strip=True)
                
                if not article_url or not title:
                    continue
                
                logger.info(f"  📌 Titre: {title}")
                logger.info(f"  🔗 URL: {article_url}")
                
                # Récupère la page de l'article
                try:
                    logger.info(f"  📄 Accès à l'article...")
                    article_response = requests.get(article_url, headers=HEADERS, timeout=30)
                    article_response.raise_for_status()
                except Exception as e:
                    logger.warning(f"  ⊘ Page inaccessible: {e}")
                    continue
                
                # Parse et trouve le PDF
                article_soup = BeautifulSoup(article_response.text, 'html.parser')
                pdf_link = article_soup.find('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
                
                if not pdf_link:
                    logger.warning(f"  ⊘ Aucun PDF trouvé sur cette page")
                    continue
                
                pdf_url = pdf_link.get('href')
                logger.info(f"  📎 PDF trouvé: {pdf_url[:60]}...")
                
                pdf_name = slugify(title) + ".pdf"
                pdf_path = RAW_DIR / pdf_name
                
                # Évite doublons
                if pdf_path.exists():
                    logger.info(f"  ⊘ Déjà téléchargé précédemment")
                    continue
                
                # Télécharge
                if download_pdf(pdf_url, pdf_name):
                    count += 1
                
                # Anti-throttling
                logger.info("")
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"  ✗ Erreur: {e}")
                continue
        
        # Résumé
        logger.info(f"\n{'='*70}")
        logger.info(f"✅ SCRAPING TERMINÉ")
        logger.info(f"  📊 PDFs téléchargés: {count}/{limit}")
        logger.info(f"  📁 Dossier: {RAW_DIR.absolute()}")
        logger.info(f"{'='*70}")
        
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Change la limite ici (par défaut 5)
    scrape_btp_cours(limit=5)
