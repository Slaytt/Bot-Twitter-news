import time
import logging
from database import init_db
from scheduler_service import start_scheduler

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting Bot Worker...")
    
    # 1. Initialisation de la base de données (et chargement des FIXED_TOPICS)
    init_db()
    
    # 2. Démarrage du planificateur
    scheduler = start_scheduler()
    
    # 3. Boucle infinie pour garder le processus en vie
    # C'est nécessaire car BackgroundScheduler tourne dans un thread secondaire.
    # Si le script principal s'arrête, le scheduler meurt aussi.
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping Bot Worker...")
        scheduler.shutdown()
        logger.info("Bot Worker stopped.")
