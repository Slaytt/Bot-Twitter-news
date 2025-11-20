import pytest
from tools.twitter import post_tweet

def test_post_tweet_success(mocker, mock_env_vars):
    """Test de la publication d'un tweet avec succès."""
    # Mock de tweepy.Client
    mock_client = mocker.patch("tools.twitter.tweepy.Client")
    mock_client_instance = mock_client.return_value
    
    # Simuler la réponse de create_tweet
    mock_response = mocker.Mock()
    mock_response.data = {"id": "123456789"}
    mock_client_instance.create_tweet.return_value = mock_response
    
    # Exécuter la fonction
    content = "Hello World"
    result = post_tweet(content)
    
    # Vérifications
    assert "Tweet posted successfully" in result
    assert "123456789" in result
    
    # Vérifier que create_tweet a été appelé avec le bon contenu
    mock_client_instance.create_tweet.assert_called_once_with(text=content)

def test_post_tweet_no_credentials(monkeypatch):
    """Test de l'erreur si les credentials sont manquants."""
    # Supprimer les variables d'environnement
    monkeypatch.delenv("TWITTER_API_KEY", raising=False)
    
    result = post_tweet("test")
    assert "Error: Twitter credentials not found" in result

def test_post_tweet_api_error(mocker, mock_env_vars):
    """Test de la gestion des erreurs de l'API Twitter."""
    # Mock pour lever une exception
    mock_client = mocker.patch("tools.twitter.tweepy.Client")
    mock_client_instance = mock_client.return_value
    mock_client_instance.create_tweet.side_effect = Exception("Twitter API Error")
    
    result = post_tweet("test")
    assert "Error posting tweet" in result
    assert "Twitter API Error" in result
