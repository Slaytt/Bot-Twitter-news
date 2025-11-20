from mcp.server.fastmcp import FastMCP
from tools.scraper import scrape_website
from tools.search import search_web as search_web_func
from tools.twitter import post_tweet as post_tweet_func
from database import init_db, add_scheduled_tweet, get_monthly_count
from scheduler_service import start_scheduler
from datetime import datetime

# Initialisation du serveur FastMCP
mcp = FastMCP("TwitterBotNews")

@mcp.tool()
async def scrape(url: str) -> str:
    """
    Scrape le contenu d'une page web.
    
    Args:
        url: L'URL de la page à visiter.
        
    Returns:
        Le titre et le contenu textuel de la page.
    """
    return await scrape_website(url)

@mcp.tool()
def search_web(query: str, max_results: int = 5) -> str:
    """
    Effectue une recherche web et retourne les résultats.
    
    Args:
        query: La requête de recherche.
        max_results: Le nombre maximum de résultats à retourner (défaut: 5).
        
    Returns:
        Une liste formatée des résultats avec titres, URLs et descriptions.
    """
    return search_web_func(query, max_results)

@mcp.tool()
def post_tweet(content: str) -> str:
    """
    Poste un tweet sur le compte Twitter configuré.
    
    Args:
        content: Le contenu du tweet (max 280 caractères).
        
    Returns:
        L'ID du tweet publié ou un message d'erreur.
        
    Note:
        Nécessite la configuration des credentials Twitter dans le fichier .env
    """
    return post_tweet_func(content)

@mcp.tool()
def schedule_tweet(content: str, run_at: str) -> str:
    """
    Programme un tweet pour une date et heure future.
    
    Args:
        content: Le contenu du tweet.
        run_at: La date et l'heure d'envoi au format ISO (ex: '2023-12-25T10:00:00').
        
    Returns:
        Confirmation de la programmation ou message d'erreur.
    """
    try:
        run_date = datetime.fromisoformat(run_at)
        tweet_id = add_scheduled_tweet(content, run_date)
        return f"Tweet scheduled successfully! ID: {tweet_id}, Time: {run_date}"
    except ValueError:
        return "Error: Invalid date format. Please use ISO format (YYYY-MM-DDTHH:MM:SS)."
    except Exception as e:
        return f"Error scheduling tweet: {str(e)}"

@mcp.tool()
def get_tweet_stats() -> str:
    """
    Retourne les statistiques d'utilisation du bot (quota mensuel).
    
    Returns:
        Le nombre de tweets envoyés ce mois-ci et le quota restant.
    """
    count = get_monthly_count()
    limit = 500
    remaining = limit - count
    return f"Monthly Usage: {count}/{limit} tweets.\nRemaining: {remaining} tweets."

from tools.content_generator import generate_tweet_content

@mcp.tool()
def generate_tweet(topic: str, context: str = "", tone: str = "professional") -> str:
    """
    Génère un tweet engageant avec l'IA Gemini.
    
    Args:
        topic: Le sujet du tweet.
        context: Contexte optionnel (ex: contenu d'un article).
        tone: Le ton souhaité (défaut: professional).
        
    Returns:
        Le contenu du tweet généré.
    """
    return generate_tweet_content(topic, source_content=context if context else None, tone=tone)

from database import add_monitored_topic, get_active_topics, delete_monitored_topic

@mcp.tool()
def monitor_topic(query: str, interval_minutes: int = 60) -> str:
    """
    Ajoute un sujet à la veille automatique.
    
    Args:
        query: Le sujet ou mot-clé à surveiller.
        interval_minutes: L'intervalle de vérification en minutes (défaut: 60).
        
    Returns:
        Confirmation de l'ajout.
    """
    topic_id = add_monitored_topic(query, interval_minutes)
    return f"Topic '{query}' added to monitoring (ID: {topic_id}, Interval: {interval_minutes}m)."

@mcp.tool()
def list_topics() -> str:
    """
    Liste les sujets actuellement surveillés.
    
    Returns:
        La liste des sujets avec leurs IDs et intervalles.
    """
    topics = get_active_topics()
    if not topics:
        return "No active topics."
    
    result = "Monitored Topics:\n"
    for t in topics:
        result += f"- ID {t['id']}: '{t['query']}' (Every {t['interval_minutes']}m, Last run: {t['last_run'] or 'Never'})\n"
    return result

@mcp.tool()
def delete_topic(topic_id: int) -> str:
    """
    Arrête la surveillance d'un sujet.
    
    Args:
        topic_id: L'ID du sujet à supprimer (voir list_topics).
    """
    delete_monitored_topic(topic_id)
    return f"Topic {topic_id} deleted."

if __name__ == "__main__":
    # Initialisation DB et Scheduler
    init_db()
    start_scheduler()
    mcp.run()
