from duckduckgo_search import DDGS

def search_web(query: str, max_results: int = 5) -> str:
    """
    Effectue une recherche web et retourne les résultats.
    
    Args:
        query: La requête de recherche.
        max_results: Le nombre maximum de résultats à retourner.
        
    Returns:
        Une chaîne formatée contenant les titres et URLs des résultats.
    """
    try:
        results = DDGS().text(query, max_results=max_results)
        formatted_results = []
        for r in results:
            formatted_results.append(f"- [{r['title']}]({r['href']})\n  {r['body']}")
        
        return "\n\n".join(formatted_results)
    except Exception as e:
        return f"Error searching for '{query}': {str(e)}"

if __name__ == "__main__":
    print(search_web("Python MCP server"))
