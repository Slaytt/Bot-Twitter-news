import tweepy
import os
from dotenv import load_dotenv

load_dotenv()

def post_tweet(content: str) -> str:
    """
    Poste un tweet sur le compte configuré.
    
    Args:
        content: Le contenu du tweet.
        
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
