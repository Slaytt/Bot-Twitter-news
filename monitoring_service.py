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
    
    potential_items = [] # Liste de {url, title, content (opt), is_tweet}
    
    # --- 1. Récupération des candidats ---
    
    if source_type == 'twitter':
        # Recherche Twitter
        tweets = search_tweets(topic['query'])
        for tweet in tweets:
            tweet_url = f"https://twitter.com/user/status/{tweet['id']}"
            potential_items.append({
                'url': tweet_url,
                'title': f"Tweet from {tweet['id']}",
                'content': tweet['text'],
                'is_tweet': True
            })
                
    elif source_type == 'specific_url':
        # Surveillance d'une page spécifique (Deep Scan)
        try:
            links = asyncio.run(get_links_from_page(topic['query']))
            for link in links:
                potential_items.append({'url': link, 'title': 'New Link', 'is_tweet': False})
        except Exception as e:
            logger.error(f"Error monitoring URL {topic['query']}: {e}")
            
    else: # web_search (défaut)
        try:
            results = DDGS().text(topic['query'], max_results=5)
            for res in results:
                potential_items.append({'url': res['href'], 'title': res['title'], 'is_tweet': False})
        except Exception as e:
            logger.error(f"Search failed for {topic['query']}: {e}")

    # --- 2. Traitement des nouveaux items ---
    
    items_processed = 0
    
    for item in potential_items:
        # Vérifier si déjà traité
        if is_url_processed(item['url']):
            continue
            
        logger.info(f"New content found: {item['url']}")
        
        # Préparation du contenu source
        source_content = item.get('content', '')
        image_url = None
        
        # Deep Scraping si nécessaire (pour les liens web)
        if not item.get('is_tweet'):
            try:
                # On scrape TOUJOURS pour avoir le contenu complet et l'image
                scrape_result = asyncio.run(scrape_website(item['url']))
                
                if isinstance(scrape_result, dict):
                    source_content = scrape_result.get('content', '')
                    image_url = scrape_result.get('image_url')
                else:
                    source_content = scrape_result
                
                # Fallback Image Search si pas d'image trouvée
                if not image_url:
                    try:
                        logger.info(f"No image found for {item['url']}, searching fallback...")
                        # Utiliser le titre ou une partie de l'URL pour la recherche
                        search_term = item.get('title') or topic['query']
                        ddgs = DDGS()
                        images = ddgs.images(search_term, max_results=1)
                        if images:
                            image_url = images[0]['image']
                            logger.info(f"Fallback image found: {image_url}")
                    except Exception as e:
                        logger.warning(f"Fallback image search failed: {e}")

                # Ignorer si contenu trop court (probablement erreur ou page vide)
                if len(source_content) < 200:
                    logger.warning(f"Content too short for {item['url']}, skipping.")
                    mark_url_processed(item['url'], topic['id']) # Marquer pour ne pas réessayer en boucle
                    continue
                    
            except Exception as e:
                logger.error(f"Failed to scrape {item['url']}: {e}")
                continue

        # --- 3. Génération du tweet ---
        
        prompt_topic = topic['query']
        if item.get('is_tweet'):
            prompt_topic = f"Réaction au tweet sur {topic['query']}"
            
        tweet_content = generate_tweet_content(
            topic=prompt_topic,
            source_content=source_content,
            tone="informative"
        )
        
        if "Error" in tweet_content:
            logger.error(f"Failed to generate tweet for {item['url']}: {tweet_content}")
            continue

        # --- 4. Planification ---
        
        # On étale les tweets si on en trouve plusieurs d'un coup (toutes les 5 min)
        delay_minutes = 5 + (items_processed * 5)
        run_at = datetime.now() + timedelta(minutes=delay_minutes)
        
        add_scheduled_tweet(tweet_content, run_at, source_url=item['url'], image_url=image_url)
        
        # --- 5. Clôture item ---
        mark_url_processed(item['url'], topic['id'])
        items_processed += 1
        
        # Limite de sécurité : max 3 tweets par cycle pour un même sujet pour éviter le spam
        if items_processed >= 3:
            break
    
    # Mise à jour du last_run global du sujet
    update_topic_last_run(topic['id'])
    if items_processed > 0:
        logger.info(f"Successfully scheduled {items_processed} tweets for {topic['query']}")
