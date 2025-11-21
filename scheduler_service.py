from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from database import get_pending_tweets, update_tweet_status, get_monthly_count, get_setting
from tools.twitter import post_tweet
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONTHLY_LIMIT = 500

def check_and_send_tweets():
    """Vérifie les tweets en attente et les envoie si le quota le permet."""
    # Vérifier si en pause
    if get_setting("pause_mode", "False") == "True":
        logger.info("Bot is in PAUSE mode. Skipping tweet check.")
        return

    logger.info("Checking for pending tweets...")
    
    pending_tweets = get_pending_tweets()
    
    if not pending_tweets:
        logger.info("No pending tweets.")
        return

    current_count = get_monthly_count()
    logger.info(f"Current monthly count: {current_count}/{MONTHLY_LIMIT}")

    for tweet in pending_tweets:
        # Vérification stricte du quota
        if current_count >= MONTHLY_LIMIT:
            logger.warning(f"Monthly limit reached ({current_count}). Skipping tweet {tweet['id']}.")
            update_tweet_status(
                tweet['id'], 
                'skipped', 
                error="Monthly limit reached (500 tweets)"
            )
            continue

        logger.info(f"Sending tweet {tweet['id']}: {tweet['content'][:30]}...")
        
        # Tentative d'envoi (avec image et thread si disponibles)
        image_url = tweet.get('image_url')
        thread_content = tweet.get('thread_content')
        result = post_tweet(tweet['content'], image_url=image_url, thread_content=thread_content)
        
        if "Error" in result:
            logger.error(f"Failed to send tweet {tweet['id']}: {result}")
            
            # Gestion spécifique du Rate Limit (429)
            if "429" in result or "Too Many Requests" in result:
                logger.warning("Rate Limit detected (429). Leaving tweet in pending state for retry later.")
                # On ne change PAS le statut, il sera repris au prochain cycle (ou on pourrait ajouter un backoff)
                # Optionnel : Mettre un message d'erreur temporaire sans changer le statut 'pending'
                update_tweet_status(tweet['id'], 'pending', error="Rate Limit (429) - Will retry later")
            else:
                update_tweet_status(tweet['id'], 'failed', error=result)
        else:
            # Extraction de l'ID (format supposé: "Tweet posted successfully! ID: 12345")
            try:
                twitter_id = result.split("ID: ")[1].strip()
            except:
                twitter_id = "unknown"
                
            logger.info(f"Tweet {tweet['id']} sent successfully. Twitter ID: {twitter_id}")
            update_tweet_status(tweet['id'], 'sent', twitter_id=twitter_id)
            current_count += 1

from monitoring_service import run_monitoring_cycle

def start_scheduler():
    """Démarre le planificateur en arrière-plan."""
    scheduler = BackgroundScheduler()
    
    # Vérifier toutes les minutes pour l'envoi des tweets
    scheduler.add_job(
        check_and_send_tweets,
        trigger=IntervalTrigger(minutes=1),
        id='tweet_sender',
        name='Check and send pending tweets',
        replace_existing=True
    )
    
    # Cycle de veille (toutes les 10 minutes)
    scheduler.add_job(
        run_monitoring_cycle,
        trigger=IntervalTrigger(minutes=1),
        id='monitoring_cycle',
        name='Run monitoring cycle',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started.")
    return scheduler
