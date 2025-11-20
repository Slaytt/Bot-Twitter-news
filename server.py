from mcp.server.fastmcp import FastMCP
from tools.scraper import scrape_website

# Initialisation du serveur FastMCP
mcp = FastMCP("TwitterBotScraper")

@mcp.tool()
async def scrape(url: str) -> str:
    """
    Scrape le contenu d'une page web.
    
    Args:
        url: L'URL de la page à visiter.
    """
    return await scrape_website(url)

if __name__ == "__main__":
    mcp.run()
