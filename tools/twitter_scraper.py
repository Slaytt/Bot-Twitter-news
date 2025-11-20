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
            try:
                # URL de recherche Twitter adaptée (Twitter peut bloquer sans login)
                # On utilise nitter.poast.org (instance alternative plus stable)
                search_url = f"https://nitter.poast.org/search?f=tweets&q={topic}%20lang%3Afr&since=&until=&near="
                
                logger.info(f"Searching for: {topic} on Nitter")
                await page.goto(search_url, wait_until="load", timeout=30000)  # 30s timeout
                
                # Attendre que les tweets se chargent
                await asyncio.sleep(3)
                
                # Nitter utilise des sélecteurs différents
                tweets = await page.query_selector_all('.timeline-item')
                logger.info(f"Found {len(tweets)} timeline items for {topic}")
                
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
                        
                        if stats_elem:
                            stats_text = await stats_elem.inner_text()
                            # Parse format: "12 retweets, 34 likes"
                            retweet_match = re.search(r'(\d+)\s*retweet', stats_text, re.IGNORECASE)
                            like_match = re.search(r'(\d+)\s*(?:like|quote)', stats_text, re.IGNORECASE)
                            
                            if retweet_match:
                                retweets = int(retweet_match.group(1))
                            if like_match:
                                likes = int(like_match.group(1))
                        
                        # Score d'engagement
                        score = likes + (retweets * 2)
                        
                        all_tweets.append({
                            'id': tweet_id,
                            'text': text,
                            'url': tweet_url,
                            'likes': likes,
                            'retweets': retweets,
                            'created_at': created_at,
                            'score': score,
                            'topic': topic
                        })
                        
                    except Exception as e:
                        logger.warning(f"Error parsing tweet: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error searching for {topic}: {e}")
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
