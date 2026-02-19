"""
Scraper pour récupérer toutes les URLs d'articles depuis les pages de catégories
Gère la pagination automatiquement
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

BASE_URL = "https://www.btp-cours.com/category/documents/document-pdf"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def scrape_category_pages(max_pages=None):
    """
    Récupère tous les liens d'articles depuis toutes les pages de la catégorie
    
    Args:
        max_pages: Limite du nombre de pages à scraper (None = toutes)
    
    Returns:
        Liste d'URLs d'articles uniques
    """
    article_urls = set()
    page = 1
    
    while True:
        if max_pages and page > max_pages:
            break
            
        # Construction de l'URL avec pagination
        if page == 1:
            url = BASE_URL
        else:
            url = f"{BASE_URL}/page/{page}/"
        
        print(f"[SCAN] Page {page}: {url}")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('article')
            
            if not articles:
                print(f"[INFO] Aucun article trouvé sur la page {page}, fin du scraping")
                break
            
            # Extraction des URLs d'articles
            found_on_page = 0
            for article in articles:
                title_el = article.find('h2')
                if not title_el:
                    continue
                    
                link = title_el.find('a')
                if not link or not link.get('href'):
                    continue
                
                article_url = link['href']
                if article_url not in article_urls:
                    article_urls.add(article_url)
                    found_on_page += 1
            
            print(f"[INFO] {found_on_page} nouveaux articles trouvés sur page {page}")
            
            # Si aucun nouvel article, on arrête
            if found_on_page == 0:
                print("[INFO] Pas de nouveaux articles, fin du scraping")
                break
            
            page += 1
            time.sleep(1)  # Anti-throttling
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"[INFO] Page {page} introuvable (404), fin du scraping")
                break
            else:
                print(f"[ERROR] Erreur HTTP sur page {page}: {e}")
                break
        except Exception as e:
            print(f"[ERROR] Erreur sur page {page}: {e}")
            break
    
    return list(article_urls)


if __name__ == "__main__":
    # Test
    urls = scrape_category_pages(max_pages=2)
    print(f"\n[SUCCESS] {len(urls)} articles trouvés au total")
    for url in urls[:5]:
        print(f"  - {url}")
