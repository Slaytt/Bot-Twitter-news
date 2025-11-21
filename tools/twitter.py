import tweepy
import os
import requests
import tempfile
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

def get_twitter_client():
    """Crée et retourne un client Twitter."""
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    if not all([api_key, api_secret, access_token, access_token_secret]):
        return None

    return tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )

def post_tweet(content: str, image_url: str = None, thread_content: str = None) -> str:
    """
    Poste un tweet sur le compte configuré.
    
    Args:
        content: Le contenu du tweet.
        image_url: URL optionnelle d'une image à attacher.
        thread_content: Contenu optionnel pour un thread (réponse).
        
    Returns:
        L'URL du tweet publié ou un message d'erreur.
    """
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    if not all([api_key, api_secret, access_token, access_token_secret]):
        return "Error: Twitter credentials not found in .env file."

    try:
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        
        media_ids = []
        
        # Si une image est fournie, la télécharger et l'uploader
        if image_url:
            try:
                # Télécharger l'image
                response = requests.get(image_url, timeout=10)
                response.raise_for_status()
                
                # Sauvegarder temporairement
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
                
                # Uploader sur Twitter (API v1.1 pour les médias)
                auth = tweepy.OAuth1UserHandler(
                    api_key,
                    api_secret,
                    access_token,
                    access_token_secret
                )
                api_v1 = tweepy.API(auth)
                media = api_v1.media_upload(tmp_path)
                media_ids.append(media.media_id)
                
                # Nettoyer le fichier temporaire
                os.unlink(tmp_path)
                
            except Exception as img_error:
                print(f"Failed to upload image: {img_error}")
                # Continue sans image si ça échoue
        
        # Fonction interne pour poster
        def attempt_post(text, media_ids=None, reply_to_id=None):
            if media_ids:
                return client.create_tweet(text=text, media_ids=media_ids, in_reply_to_tweet_id=reply_to_id)
            else:
                return client.create_tweet(text=text, in_reply_to_tweet_id=reply_to_id)

        # Vérification de la longueur et gestion des threads
        main_tweet_content = content
        
        # Si pas de thread explicite, on garde la logique automatique (fallback)
        if not thread_content:
            import re
            # Regex plus simple et robuste pour capturer les URLs
            url_pattern = r'https?://\S+'
            urls = re.findall(url_pattern, content)
            
            # Si le contenu est trop long (> 280) et qu'il y a un lien
            if len(content) > 280 and urls:
                link = urls[-1] # On prend le dernier lien (souvent la source)
                
                # On retire le lien du tweet principal
                content_without_link = content.replace(link, "").strip()
                
                # Si sans le lien c'est bon (< 280), on fait un thread
                if len(content_without_link) <= 280:
                    main_tweet_content = content_without_link
                    thread_content = f"🔗 Source : {link}"
                    print("Tweet too long. Splitting link into a thread (Auto).")

        try:
            # Post du tweet principal
            response = attempt_post(main_tweet_content, media_ids)
            main_tweet_id = response.data['id']
            result_msg = f"Tweet posted successfully! ID: {main_tweet_id}"
            
            # Post du thread si nécessaire
            if thread_content:
                try:
                    thread_response = attempt_post(thread_content, reply_to_id=main_tweet_id)
                    result_msg += f" + Thread ID: {thread_response.data['id']}"
                except Exception as thread_error:
                    print(f"Failed to post thread: {thread_error}")
                    result_msg += " (Thread failed)"
            
            return result_msg

        except tweepy.errors.Forbidden as e:
            # Si erreur 403 (souvent due à un lien bloqué ou contenu flaggé)
            if "403" in str(e) and "http" in main_tweet_content:
                print(f"⚠️ 403 Forbidden detected. Retrying without links. Error: {e}")
                
                # Retirer les liens avec regex
                clean_content = re.sub(r'http\S+', '', main_tweet_content).strip()
                
                # Retenter sans lien (et sans image si c'était le problème, mais on garde l'image pour l'instant)
                # Souvent c'est le lien dans le texte qui bloque
                try:
                    response = attempt_post(clean_content, media_ids)
                    return f"Tweet posted successfully (without links)! ID: {response.data['id']}"
                except Exception as retry_error:
                    return f"Error posting tweet (retry failed): {str(retry_error)}"
            else:
                raise e

    except tweepy.errors.TooManyRequests as e:
        print(f"⚠️ 429 Too Many Requests. Retrying in 15 minutes...")
        # Si c'est un script long, on pourrait attendre, mais ici on retourne l'erreur pour que le scheduler réessaie plus tard
        # Ou on implémente un petit retry si c'est juste un burst
        import time
        
        max_retries = 3
        retry_delay = 60 # 1 minute initial delay
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 Retry attempt {attempt+1}/{max_retries} in {retry_delay}s...")
                time.sleep(retry_delay)
                
                response = attempt_post(main_tweet_content, media_ids)
                main_tweet_id = response.data['id']
                result_msg = f"Tweet posted successfully (after retry)! ID: {main_tweet_id}"
                
                if thread_content:
                    try:
                        time.sleep(2) # Pause entre tweet et thread
                        thread_response = attempt_post(thread_content, reply_to_id=main_tweet_id)
                        result_msg += f" + Thread ID: {thread_response.data['id']}"
                    except Exception:
                        result_msg += " (Thread failed)"
                
                return result_msg
                
            except tweepy.errors.TooManyRequests:
                retry_delay *= 2 # Exponential backoff
                continue
            except Exception as retry_error:
                return f"Error posting tweet (retry failed): {str(retry_error)}"
        
        return f"Error posting tweet: 429 Too Many Requests (Max retries exceeded)"

    except Exception as e:
        return f"Error posting tweet: {str(e)}"

def search_tweets(query: str, max_results: int = 10) -> list[dict]:
    """
    Recherche des tweets récents.
    Note: Nécessite un accès API Basic ou Pro pour la recherche v2.
    """
    client = get_twitter_client()
    if not client:
        return []
        
    try:
        # search_recent_tweets est pour l'API v2
        tweets = client.search_recent_tweets(query=query, max_results=max_results, tweet_fields=['created_at', 'author_id'])
        if not tweets.data:
            return []
            
        results = []
        for tweet in tweets.data:
            results.append({
                'id': tweet.id,
                'text': tweet.text,
                'created_at': tweet.created_at
            })
        return results
    except Exception as e:
        # Fallback ou log
        print(f"Error searching tweets: {e}")
        return []

def get_top_french_tech_tweets() -> list[dict]:
    """
    Récupère les 3 tweets français les plus populaires (Likes + RTs) des dernières 12h
    sur les sujets : IA, Twitch, Crypto, Jeux Vidéo.
    Optimisé pour n'utiliser qu'une seule requête API.
    """
    client = get_twitter_client()
    if not client:
        return []

    # Requête combinée
    query = '(IA OR Twitch OR Crypto OR "Jeux Vidéo") lang:fr -is:retweet -is:reply'
    
    try:
        # Récupérer plus de tweets pour avoir un bon échantillon à trier (max 100 par requête Basic)
        # On demande les métriques publiques pour le tri
        tweets = client.search_recent_tweets(
            query=query,
            max_results=50, # Suffisant pour avoir un top 3 pertinent sans trop charger
            tweet_fields=['created_at', 'public_metrics', 'author_id', 'id', 'text']
        )
        
        if not tweets.data:
            return []
            
        processed_tweets = []
        now = datetime.now(timezone.utc)
        
        for tweet in tweets.data:
            # Filtrage 12h (l'API v2 filtre par défaut sur 7 jours, on affine ici)
            created_at = tweet.created_at
            if (now - created_at) > timedelta(hours=12):
                continue
                
            metrics = tweet.public_metrics
            engagement_score = metrics['like_count'] + (metrics['retweet_count'] * 2) # RT vaut double
            
            processed_tweets.append({
                'id': tweet.id,
                'text': tweet.text,
                'created_at': created_at,
                'likes': metrics['like_count'],
                'retweets': metrics['retweet_count'],
                'score': engagement_score,
                'url': f"https://twitter.com/user/status/{tweet.id}"
            })
            
        # Tri par score décroissant
        processed_tweets.sort(key=lambda x: x['score'], reverse=True)
        
        # Top 3
        return processed_tweets[:3]
        
    except Exception as e:
        print(f"Error fetching top tweets: {e}")
        return []

if __name__ == "__main__":
    # Ne fonctionnera que si .env est configuré
    print(post_tweet("Hello from MCP Bot!"))
