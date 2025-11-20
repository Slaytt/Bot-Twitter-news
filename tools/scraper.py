import asyncio
from playwright.async_api import async_playwright

async def scrape_website(url: str) -> str:
    """
    Scrape le contenu textuel d'un site web donné.
    
    Args:
        url: L'URL du site à scraper.
        
    Returns:
        Le contenu textuel de la page ou un message d'erreur.
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)
            # Attendre que le contenu soit chargé (simple attente réseau ici, peut être amélioré)
            await page.wait_for_load_state("networkidle")
            
            content = await page.inner_text("body")
            title = await page.title()
            
            await browser.close()
            
            return f"Title: {title}\n\nContent:\n{content}"
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"

if __name__ == "__main__":
    # Test simple si exécuté directement
    print(asyncio.run(scrape_website("https://example.com")))
