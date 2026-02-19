"""
Scraper pour un article individuel du site BTP
Retourne les données structurées pour le script principal
"""

import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def scrape_article(url):
    """
    Scrape un article et retourne ses données structurées
    
    Returns:
        dict: {
            'title': str,
            'content_html': str,
            'pdf_urls': list,
            'image_urls': list
        }
    """
    result = {
        'title': '',
        'content_html': '',
        'pdf_urls': [],
        'image_urls': []
    }
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraction du titre
        title_tag = soup.find('h1') or soup.find('h2', class_='entry-title')
        result['title'] = title_tag.get_text(strip=True) if title_tag else 'article'
        
        # Extraction du contenu HTML
        content_div = soup.find('div', class_='entry-content') or soup.find('article')
        if content_div:
            result['content_html'] = str(content_div)
        
        # Extraction des liens PDF
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        result['pdf_urls'] = [link.get('href') for link in pdf_links if link.get('href')]
        
        # Extraction des images
        images = soup.find_all('img', src=True)
        result['image_urls'] = [img.get('src') for img in images if img.get('src')]
        
        print(f"[PARSE] {result['title']} - {len(result['pdf_urls'])} PDF(s), {len(result['image_urls'])} image(s)")
        
    except Exception as e:
        print(f"[ERROR] Échec scraping {url}: {e}")
    
    return result


if __name__ == "__main__":
    # Test
    test_url = "https://www.btp-cours.com/concept-constructif-panneau-sandwich/"
    data = scrape_article(test_url)
    print(f"\nTitre: {data['title']}")
    print(f"PDFs: {data['pdf_urls']}")
    print(f"Images: {len(data['image_urls'])} trouvées")
