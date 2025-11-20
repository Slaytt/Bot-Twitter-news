import tweepy
import os
import requests
import tempfile
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

def post_tweet(content: str, image_url: str = None) -> str:
    """
    Poste un tweet sur le compte configuré.
    
    Args:
        content: Le contenu du tweet.
        image_url: URL optionnelle d'une image à attacher.
        
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
        
        # Poster le tweet (avec ou sans image)
        if media_ids:
            response = client.create_tweet(text=content, media_ids=media_ids)
        else:
            response = client.create_tweet(text=content)
        
        return f"Tweet posted successfully! ID: {response.data['id']}"
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

if __name__ == "__main__":
    # Ne fonctionnera que si .env est configuré
    print(post_tweet("Hello from MCP Bot!"))
