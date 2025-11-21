from playwright.async_api import async_playwright
import asyncio
import logging
from duckduckgo_search import DDGS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def search_web(query: str, max_results: int = 5) -> str:
    """
    Effectue une recherche web via DuckDuckGo et retourne les résultats formatés.
    """
    try:
        logger.info(f"Searching web for: {query}")
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            
        if not results:
            return "No results found."
            
        formatted_results = []
        for i, r in enumerate(results, 1):
            formatted_results.append(f"{i}. {r['title']}\n   URL: {r['href']}\n   {r['body']}\n")
            
        return "\n".join(formatted_results)
    except Exception as e:
        logger.error(f"Error searching web: {e}")
        return f"Error performing search: {str(e)}"

async def search_images_playwright(query: str, max_results: int = 3) -> list[dict]:
    """
    Recherche des images sur DuckDuckGo via Playwright (Bulldozer method).
    Bypasse les rate limits de l'API.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            # URL DuckDuckGo Images
            url = f"https://duckduckgo.com/?q={query}&t=h_&iax=images&ia=images"
            logger.info(f"Searching images for: {query}")
            
            await page.goto(url, wait_until="networkidle", timeout=15000)
            
            # Attendre que les images chargent
            await page.wait_for_selector('.tile--img__img', timeout=5000)
            
            # Extraire les images
            images = await page.query_selector_all('.tile--img__img')
            
            results = []
            for img in images[:max_results]:
                src = await img.get_attribute('src')
                # DuckDuckGo utilise souvent des URLs proxy, on essaie de chopper l'original si possible
                # Mais src fonctionne généralement
                if src and src.startswith('//'):
                    src = f"https:{src}"
                
                if src:
                    results.append({'image': src, 'title': query})
            
            return results
            
        except Exception as e:
            logger.error(f"Error scraping images: {e}")
            return []
        finally:
            await browser.close()

if __name__ == "__main__":
    async def test():
        res = await search_images_playwright("Elon Musk")
        print(res)
    asyncio.run(test())
