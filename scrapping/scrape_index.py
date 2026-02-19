import requests
from bs4 import BeautifulSoup

BASE_URL = "https://geniecivilpdf.com/pdf/"


def get_article_links():
    r = requests.get(BASE_URL, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    links = set()
    for a in soup.select("a.featured-link"):
        href = a.get("href")
        if href and href.startswith("https://geniecivilpdf.com/"):
            links.add(href)

    return list(links)


if __name__ == "__main__":
    urls = get_article_links()
    print(f"{len(urls)} articles trouvés")
    for u in urls[:5]:
        print(u)
