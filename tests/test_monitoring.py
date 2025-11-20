import pytest
from monitoring_service import run_monitoring_cycle

def test_monitoring_cycle_full_flow(mocker):
    """Test du cycle complet de veille."""
    # Mocks DB
    mock_get_topics = mocker.patch("monitoring_service.get_active_topics")
    mock_is_processed = mocker.patch("monitoring_service.is_url_processed")
    mock_mark_processed = mocker.patch("monitoring_service.mark_url_processed")
    mock_update_last_run = mocker.patch("monitoring_service.update_topic_last_run")
    mock_add_tweet = mocker.patch("monitoring_service.add_scheduled_tweet")
    
    # Mocks Tools
    mock_ddgs = mocker.patch("monitoring_service.DDGS")
    mock_generate = mocker.patch("monitoring_service.generate_tweet_content")
    mock_asyncio_run = mocker.patch("monitoring_service.asyncio.run")
    
    # Configuration
    mock_get_topics.return_value = [
        {'id': 1, 'query': 'AI News', 'interval_minutes': 60, 'last_run': None}
    ]
    
    # Search results
    mock_ddgs_instance = mock_ddgs.return_value
    mock_ddgs_instance.text.return_value = [
        {'href': 'http://example.com/article', 'title': 'New AI Model'}
    ]
    
    mock_is_processed.return_value = False # URL non traitée
    mock_asyncio_run.return_value = "Contenu de l'article" # Résultat du scrape
    mock_generate.return_value = "Tweet généré sur l'IA"
    
    # Exécution
    run_monitoring_cycle()
    
    # Vérifications
    mock_ddgs_instance.text.assert_called_with('AI News', max_results=5)
    mock_asyncio_run.assert_called() # Vérifie que scrape a été appelé via asyncio.run
    mock_generate.assert_called()
    mock_add_tweet.assert_called()
    mock_mark_processed.assert_called_with('http://example.com/article', 1)
    mock_update_last_run.assert_called_with(1)

def test_monitoring_skips_processed_urls(mocker):
    """Test que les URLs déjà traitées sont ignorées."""
    mock_get_topics = mocker.patch("monitoring_service.get_active_topics")
    mock_is_processed = mocker.patch("monitoring_service.is_url_processed")
    mock_ddgs = mocker.patch("monitoring_service.DDGS")
    mock_update_last_run = mocker.patch("monitoring_service.update_topic_last_run")
    mock_scrape = mocker.patch("monitoring_service.scrape_website")
    
    mock_get_topics.return_value = [{'id': 1, 'query': 'AI', 'interval_minutes': 60, 'last_run': None}]
    mock_ddgs.return_value.text.return_value = [{'href': 'http://old.com', 'title': 'Old News'}]
    mock_is_processed.return_value = True # Déjà traité
    
    run_monitoring_cycle()
    
    # Vérifier qu'on n'a PAS scrapé ni généré
    mock_scrape.assert_not_called()
    # Mais on a quand même mis à jour le last_run car pas de nouvelles URLs
    mock_update_last_run.assert_called_with(1)
