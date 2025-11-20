import asyncio
import logging
from datetime import datetime, timedelta
from duckduckgo_search import DDGS
from database import (
    get_active_topics, update_topic_last_run, is_url_processed, 
    mark_url_processed, add_scheduled_tweet
)
from tools.scraper import scrape_website
from tools.content_generator import generate_tweet_content

logger = logging.getLogger(__name__)

def run_monitoring_cycle():
    """
    Cycle principal de veille.
    Parcourt tous les sujets actifs et lance le traitement si l'intervalle est écoulé.
    """
    logger.info("Starting monitoring cycle...")
    try:
        topics = get_active_topics()
        
        for topic in topics:
            try:
                process_topic(topic)
            except Exception as e:
                logger.error(f"Error processing topic {topic['query']}: {e}")
    except Exception as e:
        logger.error(f"Critical error in monitoring cycle: {e}")

def process_topic(topic):
    """Traite un sujet spécifique."""
    # Vérification de l'intervalle
    last_run = topic['last_run']
    if last_run:
        # last_run est une string ou datetime selon le driver sqlite, on assure le coup
        if isinstance(last_run, str):
            last_run_date = datetime.fromisoformat(last_run)
        else:
            last_run_date = last_run
            
        next_run = last_run_date + timedelta(minutes=topic['interval_minutes'])
        if datetime.now() < next_run:
            return # Trop tôt pour relancer

    logger.info(f"Processing topic: {topic['query']}")
    
    # 1. Recherche de nouveaux contenus
    # On utilise DDGS directement pour avoir les métadonnées (URL, titre)
    try:
        results = DDGS().text(topic['query'], max_results=5)
    except Exception as e:
        logger.error(f"Search failed for {topic['query']}: {e}")
        return
    
    target_url = None
    target_title = None
    
    # Trouver la première URL non traitée
    for res in results:
        url = res['href']
        if not is_url_processed(url):
            target_url = url
            target_title = res['title']
            break
            
    if not target_url:
        logger.info(f"No new URLs found for {topic['query']}")
        update_topic_last_run(topic['id'])
        return

    logger.info(f"Found new URL: {target_url}")
    
    # 2. Scraping du contenu
    try:
        # scrape_website est async, on l'exécute de manière synchrone ici
        scraped_content = asyncio.run(scrape_website(target_url))
    except Exception as e:
        logger.error(f"Failed to scrape {target_url}: {e}")
        # On pourrait marquer l'URL comme "failed" pour ne pas réessayer en boucle, 
        # mais pour l'instant on laisse pour réessayer plus tard ou passer à la suivante
        return

    # 3. Génération du tweet via IA
    tweet_content = generate_tweet_content(
        topic=f"{topic['query']}: {target_title}",
        source_content=scraped_content,
        tone="informative"
    )
    
    if "Error" in tweet_content:
        logger.error(f"Failed to generate tweet: {tweet_content}")
        return

    # 4. Planification du tweet
    # On programme pour dans 5 minutes pour laisser le temps de vérifier si besoin
    run_at = datetime.now() + timedelta(minutes=5)
    add_scheduled_tweet(tweet_content, run_at)
    
    # 5. Mise à jour de l'état
    mark_url_processed(target_url, topic['id'])
    update_topic_last_run(topic['id'])
    
    logger.info(f"Successfully scheduled tweet for {topic['query']}")
