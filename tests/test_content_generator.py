import pytest
from tools.content_generator import generate_tweet_content

def test_generate_tweet_success(mocker, monkeypatch):
    """Test de la génération de tweet avec succès."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    
    # Mock de GenerativeModel
    mock_model = mocker.patch("tools.content_generator.genai.GenerativeModel")
    mock_instance = mock_model.return_value
    
    # Mock de la réponse
    mock_response = mocker.Mock()
    mock_response.text = "Ceci est un tweet généré par IA #AI #Tech"
    mock_instance.generate_content.return_value = mock_response
    
    # Exécution
    result = generate_tweet_content("AI", tone="fun")
    
    # Vérifications
    assert result == "Ceci est un tweet généré par IA #AI #Tech"
    mock_instance.generate_content.assert_called_once()
    
    # Vérifier que le prompt contient les éléments clés
    args, _ = mock_instance.generate_content.call_args
    prompt = args[0]
    assert "AI" in prompt
    assert "fun" in prompt
    assert "280 caractères" in prompt

def test_generate_tweet_no_key(monkeypatch):
    """Test erreur si pas de clé API."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = generate_tweet_content("test")
    assert "Error: GEMINI_API_KEY not found" in result

def test_generate_tweet_api_error(mocker, monkeypatch):
    """Test erreur API."""
    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    
    mock_model = mocker.patch("tools.content_generator.genai.GenerativeModel")
    mock_instance = mock_model.return_value
    mock_instance.generate_content.side_effect = Exception("API Error")
    
    result = generate_tweet_content("test")
    assert "Error generating content" in result
