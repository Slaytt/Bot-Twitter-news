import pytest
from scheduler_service import check_and_send_tweets

def test_scheduler_sends_tweet_when_quota_ok(mocker):
    """Test que le scheduler envoie le tweet si le quota est OK."""
    # Mocks
    mock_get_pending = mocker.patch("scheduler_service.get_pending_tweets")
    mock_get_count = mocker.patch("scheduler_service.get_monthly_count")
    mock_post = mocker.patch("scheduler_service.post_tweet")
    mock_update = mocker.patch("scheduler_service.update_tweet_status")
    
    # Configuration
    mock_get_pending.return_value = [{'id': 1, 'content': 'Test Tweet'}]
    mock_get_count.return_value = 100 # Quota OK (< 500)
    mock_post.return_value = "Tweet posted successfully! ID: 12345"
    
    # Exécution
    check_and_send_tweets()
    
    # Vérifications
    mock_post.assert_called_once_with('Test Tweet')
    mock_update.assert_called_once_with(1, 'sent', twitter_id='12345')

def test_scheduler_skips_tweet_when_quota_exceeded(mocker):
    """Test que le scheduler n'envoie PAS le tweet si le quota est dépassé."""
    # Mocks
    mock_get_pending = mocker.patch("scheduler_service.get_pending_tweets")
    mock_get_count = mocker.patch("scheduler_service.get_monthly_count")
    mock_post = mocker.patch("scheduler_service.post_tweet")
    mock_update = mocker.patch("scheduler_service.update_tweet_status")
    
    # Configuration
    mock_get_pending.return_value = [{'id': 1, 'content': 'Test Tweet'}]
    mock_get_count.return_value = 500 # Quota ATTEINT
    
    # Exécution
    check_and_send_tweets()
    
    # Vérifications
    mock_post.assert_not_called() # Ne doit pas poster
    mock_update.assert_called_once()
    args, kwargs = mock_update.call_args
    assert args[0] == 1
    assert args[1] == 'skipped'
    assert "Monthly limit reached" in kwargs['error']

def test_scheduler_handles_post_error(mocker):
    """Test que le scheduler gère les erreurs d'envoi."""
    # Mocks
    mock_get_pending = mocker.patch("scheduler_service.get_pending_tweets")
    mock_get_count = mocker.patch("scheduler_service.get_monthly_count")
    mock_post = mocker.patch("scheduler_service.post_tweet")
    mock_update = mocker.patch("scheduler_service.update_tweet_status")
    
    # Configuration
    mock_get_pending.return_value = [{'id': 1, 'content': 'Test Tweet'}]
    mock_get_count.return_value = 100
    mock_post.return_value = "Error: API Timeout"
    
    # Exécution
    check_and_send_tweets()
    
    # Vérifications
    mock_post.assert_called_once()
    mock_update.assert_called_once()
    args, kwargs = mock_update.call_args
    assert args[1] == 'failed'
    assert "API Timeout" in kwargs['error']
