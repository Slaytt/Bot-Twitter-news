import asyncio
from playwright.async_api import async_playwright

async def scrape_website(url: str) -> dict:
    """
    Scrape le contenu principal d'une page web.
    Extrait le titre, la date, l'auteur, le contenu principal et l'image.
    
    Returns:
        dict: {'content': str, 'image_url': str | None}
    """
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
            
            # Extraction des métadonnées
            title = await page.title()
            
            # Essayer d'extraire l'auteur
            author = await page.evaluate("""
                () => {
                    const authorMeta = document.querySelector('meta[name="author"], meta[property="article:author"]');
                    if (authorMeta) return authorMeta.content;
                    
                    const authorSpan = document.querySelector('[rel="author"], .author, .author-name');
                    if (authorSpan) return authorSpan.innerText;
                    
                    return null;
                }
            """)
            
            # Essayer d'extraire la date
            date = await page.evaluate("""
                () => {
                    const dateMeta = document.querySelector('meta[property="article:published_time"], meta[name="publish-date"]');
                    if (dateMeta) return dateMeta.content;
                    
                    const timeTag = document.querySelector('time[datetime]');
                    if (timeTag) return timeTag.getAttribute('datetime');
                    
                    return null;
                }
            """)
            
            # Extraction du contenu principal
            content = await page.evaluate("""
                () => {
                    // Cibler le contenu principal de l'article
                    const selectors = [
                        'article',
                        'main article',
                        '[role="main"] article',
                        '.article-content',
                        '.post-content',
                        '.entry-content',
                        'main',
                        '#content'
                    ];
                    
                    let mainContent = null;
                    for (const selector of selectors) {
                        mainContent = document.querySelector(selector);
                        if (mainContent) break;
                    }
                    
                    if (!mainContent) {
                        mainContent = document.body;
                    }
                    
                    // Supprimer les éléments indésirables
                    const unwanted = mainContent.querySelectorAll('script, style, nav, header, footer, aside, .ad, .advertisement, .social-share, .comments');
                    unwanted.forEach(el => el.remove());
                    
                    // Extraire le texte clean
                    return mainContent.innerText;
                }
            """)
            
            # Extraction de l'image principale
            image_url = await page.evaluate("""
                () => {
                    // Chercher l'image Open Graph (meilleure qualité)
                    const ogImage = document.querySelector('meta[property="og:image"], meta[name="twitter:image"]');
                    if (ogImage && ogImage.content) return ogImage.content;
                    
                    // Sinon, chercher la première image dans l'article
                    const articleImages = document.querySelectorAll('article img, main img, .article-content img, .post-content img');
                    if (articleImages.length > 0) {
                        return articleImages[0].src;
                    }
                    
                    return null;
                }
            """)
            
            # Formatage du résultat
            result = f"Title: {title}\n"
            if author:
                result += f"Author: {author}\n"
            
            is_recent = True
            if date:
                result += f"Published: {date}\n"
                try:
                    from datetime import datetime, timedelta
                    from dateutil import parser
                    import pytz
                    
                    # Parse la date (supporte plusieurs formats ISO, etc.)
                    pub_date = parser.parse(date)
                    
                    # Gestion des timezones pour la comparaison
                    now = datetime.now(pytz.utc)
                    
                    if pub_date.tzinfo is None:
                        # Si la date n'a pas de timezone, on assume UTC
                        pub_date = pub_date.replace(tzinfo=pytz.utc)
                    
                    # Convertir en UTC pour la comparaison
                    pub_date_utc = pub_date.astimezone(pytz.utc)
                        
                    # Vérifier si l'article a plus de 7 jours
                    if now - pub_date_utc > timedelta(days=7):
                        is_recent = False
                        print(f"⚠️ Article ignoré (trop vieux) : {date}")
                except Exception as e:
                    print(f"⚠️ Impossible de parser la date {date}: {e}")
                    # En cas de doute, on garde l'article
                    pass

            if not is_recent:
                return {
                    'content': None,
                    'image_url': None,
                    'error': 'Article too old (> 7 days)'
                }

            result += f"\nContent:\n{content[:3000]}"  # Limiter à 3000 caractères
            
            return {
                'content': result,
                'image_url': image_url
            }
            
    except Exception as e:
        return {
            'content': f"Error scraping {url}: {str(e)}",
            'image_url': None
        }
    finally:
        if browser:
            await browser.close()

async def get_links_from_page(url: str) -> list[str]:
    """Extrait tous les liens d'une page."""
    browser = None # Initialize browser to None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
            
            links = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a')).map(a => a.href)
            """)
            
            # Filtrer les liens vides ou javascript
            valid_links = [l for l in links if l and l.startswith('http')]
            return list(set(valid_links)) # Unique links
    except Exception as e:
        print(f"Error getting links from {url}: {str(e)}")
        return []
    finally:
        if browser:
            await browser.close()

if __name__ == "__main__":
    # Test simple si exécuté directement
    print(asyncio.run(scrape_website("https://example.com")))
