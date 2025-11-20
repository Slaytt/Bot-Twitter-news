import pytest
import sys
import os

# Ajouter le répertoire racine au PYTHONPATH pour pouvoir importer les modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Fixture pour définir des variables d'environnement de test."""
    monkeypatch.setenv("TWITTER_API_KEY", "test_key")
    monkeypatch.setenv("TWITTER_API_SECRET", "test_secret")
    monkeypatch.setenv("TWITTER_ACCESS_TOKEN", "test_token")
    monkeypatch.setenv("TWITTER_ACCESS_TOKEN_SECRET", "test_token_secret")
