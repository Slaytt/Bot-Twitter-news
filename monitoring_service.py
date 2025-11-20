import asyncio
import logging
from datetime import datetime, timedelta
from duckduckgo_search import DDGS
from database import (
    get_active_topics, update_topic_last_run, is_url_processed, 
    mark_url_processed, add_scheduled_tweet
)
from tools.twitter import search_tweets
from tools.scraper import scrape_website, get_links_from_page
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
    """Traite un sujet spécifique selon son type."""
    # Vérification de l'intervalle
    last_run = topic['last_run']
    if last_run:
        if isinstance(last_run, str):
            last_run_date = datetime.fromisoformat(last_run)
        else:
            last_run_date = last_run
            
        next_run = last_run_date + timedelta(minutes=topic['interval_minutes'])
        if datetime.now() < next_run:
            return # Trop tôt

    source_type = topic.get('source_type', 'web_search')
    logger.info(f"Processing topic: {topic['query']} (Type: {source_type})")
    
    found_item = None # {url, title, content (optional), is_tweet}
    
    # --- 1. Récupération du contenu selon le type ---
    
    if source_type == 'twitter':
        # Recherche Twitter
        tweets = search_tweets(topic['query'])
        for tweet in tweets:
            tweet_url = f"https://twitter.com/user/status/{tweet['id']}"
            if not is_url_processed(tweet_url):
                found_item = {
                    'url': tweet_url,
                    'title': f"Tweet from {tweet['id']}",
                    'content': tweet['text'],
                    'is_tweet': True
                }
                break
                
    elif source_type == 'specific_url':
        # Surveillance d'une page spécifique
        try:
            links = asyncio.run(get_links_from_page(topic['query']))
            # On cherche le premier nouveau lien
            for link in links:
                if not is_url_processed(link):
                    found_item = {'url': link, 'title': 'New Link', 'is_tweet': False}
                    break
        except Exception as e:
            logger.error(f"Error monitoring URL {topic['query']}: {e}")
            
    else: # web_search (défaut)
        try:
            results = DDGS().text(topic['query'], max_results=5)
            for res in results:
                if not is_url_processed(res['href']):
                    found_item = {'url': res['href'], 'title': res['title'], 'is_tweet': False}
                    break
        except Exception as e:
            logger.error(f"Search failed for {topic['query']}: {e}")

    # --- 2. Traitement du contenu trouvé ---

    if not found_item:
        logger.info(f"No new content for {topic['query']}")
        update_topic_last_run(topic['id'])
        return

    logger.info(f"Found new content: {found_item['url']}")
    
    # Scraping si nécessaire (si ce n'est pas un tweet et qu'on n'a pas le contenu)
    source_content = found_item.get('content')
    if not source_content and not found_item.get('is_tweet'):
        try:
            source_content = asyncio.run(scrape_website(found_item['url']))
        except Exception as e:
            logger.error(f"Failed to scrape {found_item['url']}: {e}")
            return

    # --- 3. Génération du tweet ---
    
    prompt_topic = topic['query']
    if found_item.get('is_tweet'):
        prompt_topic = f"Réaction au tweet sur {topic['query']}"
        
    tweet_content = generate_tweet_content(
        topic=prompt_topic,
        source_content=source_content,
        tone="informative"
    )
    
    if "Error" in tweet_content:
        logger.error(f"Failed to generate tweet: {tweet_content}")
        return

    # --- 4. Planification ---
    
    run_at = datetime.now() + timedelta(minutes=5)
    add_scheduled_tweet(tweet_content, run_at, source_url=found_item['url'])
    
    # --- 5. Clôture ---
    
    mark_url_processed(found_item['url'], topic['id'])
    update_topic_last_run(topic['id'])
    
    logger.info(f"Successfully scheduled tweet for {topic['query']}")
