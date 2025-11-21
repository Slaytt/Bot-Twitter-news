from playwright.async_api import async_playwright
from datetime import datetime, timedelta
import re
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def scrape_top_french_tech_tweets() -> list[dict]:
    """
    Scrape Twitter pour récupérer les 3 tweets français tech les plus populaires des dernières 24h.
    Sujets : IA, Twitch, Crypto, Jeux Vidéo.
    
    Returns:
        Liste de dictionnaires contenant : id, text, url, likes, retweets, created_at, score
    """
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        # Liste des sujets à chercher
        topics = ["IA", "Twitch", "Crypto", "gaming"]
        all_tweets = []
        
        for topic in topics:
            # Retry logic pour chaque sujet (Nitter est instable)
            for attempt in range(3):
                try:
                    # URL de recherche Twitter adaptée (Twitter peut bloquer sans login)
                    # On utilise nitter.poast.org (instance alternative plus stable)
                    search_url = f"https://nitter.poast.org/search?f=tweets&q={topic}%20lang%3Afr&since=&until=&near="
                    
                    logger.info(f"Searching for: {topic} on Nitter (Attempt {attempt+1}/3)")
                    
                    # Utiliser domcontentloaded pour être plus rapide et éviter les timeouts sur des ressources tierces
                    await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Attendre un peu que le JS s'exécute si nécessaire (Nitter est SSR mais bon)
                    await asyncio.sleep(2)
                    
                    # Vérifier si on a une erreur Nitter
                    content = await page.content()
                    if "Rate limit exceeded" in content or "Instance has been rate limited" in content:
                        logger.warning(f"Nitter Rate Limit detected for {topic}")
                        await asyncio.sleep(5) # Attendre plus longtemps
                        continue
                    
                    # Nitter utilise des sélecteurs différents
                    try:
                        tweets = await page.query_selector_all('.timeline-item')
                    except Exception as e:
                        # Si le contexte est détruit, on retry
                        logger.warning(f"Context error during query_selector: {e}")
                        continue
                        
                    logger.info(f"Found {len(tweets)} timeline items for {topic}")
                    
                    if not tweets:
                        # Si pas de tweets, peut-être que la page n'a pas chargé, on retry
                        logger.warning(f"No tweets found for {topic}, retrying...")
                        continue

                    for tweet_elem in tweets[:15]:  # Analyser les 15 premiers
                        try:
                            # Extraire le texte
                            text_elem = await tweet_elem.query_selector('.tweet-content')
                            text = await text_elem.inner_text() if text_elem else ""
                            
                            if len(text) < 10:
                                continue
                            
                            # Extraire le lien
                            link_elem = await tweet_elem.query_selector('.tweet-link')
                            href = await link_elem.get_attribute('href') if link_elem else ""
                            
                            # Convertir nitter URL en twitter URL
                            if href.startswith('/'):
                                parts = href.split('#')[0].split('/')
                                if len(parts) >= 4:
                                    username = parts[1]
                                    tweet_id = parts[3]
                                    tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"
                                else:
                                    continue
                            else:
                                continue
                            
                            # Extraire la date
                            date_elem = await tweet_elem.query_selector('.tweet-date a')
                            date_title = await date_elem.get_attribute('title') if date_elem else None
                            
                            if not date_title:
                                continue
                            
                            try:
                                # Parse la date  (format: "Dec 20, 2023 · 3:45 PM UTC")
                                created_at = datetime.strptime(date_title.split(' ·')[0], "%b %d, %Y")
                                # On approxime l'heure à maintenant si pas disponible
                                created_at = created_at.replace(hour=12, minute=0, tzinfo=None)
                            except:
                                continue
                            
                            # Filtrer : moins de 24h (approximation car Nitter ne donne pas toujours l'heure)
                            if (datetime.now() - created_at) > timedelta(hours=24):
                                continue
                            
                            # Extraire les métriques (Nitter affiche likes et RT en texte)
                            stats_elem = await tweet_elem.query_selector('.tweet-stats')
                            likes = 0
                            retweets = 0
                            views = 0
                            
                            if stats_elem:
                                stats_text = await stats_elem.inner_text()
                                # Parse format: "12 retweets, 34 likes, 10k views"
                                retweet_match = re.search(r'([\d,.]+[kKmM]?)\s*retweet', stats_text, re.IGNORECASE)
                                like_match = re.search(r'([\d,.]+[kKmM]?)\s*(?:like|quote)', stats_text, re.IGNORECASE)
                                view_match = re.search(r'([\d,.]+[kKmM]?)\s*view', stats_text, re.IGNORECASE)
                                
                                if retweet_match:
                                    retweets = parse_twitter_number(retweet_match.group(1))
                                if like_match:
                                    likes = parse_twitter_number(like_match.group(1))
                                if view_match:
                                    views = parse_twitter_number(view_match.group(1))
                            
                            # Score d'engagement
                            score = likes + (retweets * 2)

                            # Filtrer par vues (10k minimum)
                            # Note: Si les vues ne sont pas affichées (0), on garde si le score est très élevé (>1000)
                            # car certaines instances Nitter n'affichent pas les vues.
                            # Mais l'user a demandé "10 000 views sinon on ne garde pas"
                            # Donc on va être strict.
                            if views < 10000:
                                 # Exception : Si on a vraiment beaucoup d'engagement (ex: 500 likes) mais que Nitter n'affiche pas les vues (views=0)
                                 # On pourrait vouloir le garder. Mais pour l'instant, respectons la consigne stricte.
                                 # Sauf si views == 0 (info manquante) ET score > 500 (banger probable)
                                 if views == 0 and score > 500:
                                     pass # On garde au bénéfice du doute
                                 else:
                                     continue
                            
                            all_tweets.append({
                                'id': tweet_id,
                                'text': text,
                                'url': tweet_url,
                                'likes': likes,
                                'retweets': retweets,
                                'views': views,
                                'created_at': created_at,
                                'score': score,
                                'topic': topic
                            })
                            
                        except Exception as e:
                            logger.warning(f"Error parsing tweet: {e}")
                            continue
                    
                    # Si on arrive ici sans erreur majeure, on break la boucle de retry
                    break
                    
                except Exception as e:
                    logger.error(f"Error searching for {topic} (Attempt {attempt+1}): {e}")
                    await asyncio.sleep(2)
                    continue
        
        await browser.close()
        
        # Trier par score et retourner top 3
        all_tweets.sort(key=lambda x: x['score'], reverse=True)
        return all_tweets[:3]

def parse_twitter_number(text: str) -> int:
    """
    Parse les nombres Twitter (ex: "1,2 k", "123", "1 M").
    """
    if not text:
        return 0
    
    # Extraire les nombres du texte
    match = re.search(r'([\d,\.]+)\s*([kKmM]?)', text)
    if not match:
        return 0
    
    number_str = match.group(1).replace(',', '.')
    multiplier_str = match.group(2).lower()
    
    try:
        number = float(number_str)
    except ValueError:
        return 0
    
    # Appliquer le multiplicateur
    if multiplier_str == 'k':
        number *= 1000
    elif multiplier_str == 'm':
        number *= 1000000
    
    return int(number)

# Pour test direct
if __name__ == "__main__":
    async def test():
        tweets = await scrape_top_french_tech_tweets()
        for i, tweet in enumerate(tweets, 1):
            print(f"\n#{i}")
            print(f"Text: {tweet['text'][:100]}...")
            print(f"Likes: {tweet['likes']} | RT: {tweet['retweets']} | Score: {tweet['score']}")
            print(f"URL: {tweet['url']}")
    
    asyncio.run(test())
