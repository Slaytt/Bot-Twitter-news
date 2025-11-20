import pytest
from tools.search import search_web

def test_search_web_success(mocker):
    """Test de la recherche web avec succès."""
    # Mock de la classe DDGS et de sa méthode text
    mock_ddgs = mocker.patch("tools.search.DDGS")
    mock_ddgs_instance = mock_ddgs.return_value
    
    # Simuler des résultats de recherche
    mock_results = [
        {"title": "Test Result 1", "href": "https://example.com/1", "body": "Description 1"},
        {"title": "Test Result 2", "href": "https://example.com/2", "body": "Description 2"}
    ]
    mock_ddgs_instance.text.return_value = mock_results
    
    # Exécuter la fonction
    result = search_web("test query", max_results=2)
    
    # Vérifications
    assert "Test Result 1" in result
    assert "https://example.com/1" in result
    assert "Description 1" in result
    assert "Test Result 2" in result
    
    # Vérifier que DDGS().text a été appelé avec les bons arguments
    mock_ddgs_instance.text.assert_called_once_with("test query", max_results=2)

def test_search_web_error(mocker):
    """Test de la gestion des erreurs lors de la recherche."""
    # Mock pour lever une exception
    mock_ddgs = mocker.patch("tools.search.DDGS")
    mock_ddgs_instance = mock_ddgs.return_value
    mock_ddgs_instance.text.side_effect = Exception("API Error")
    
    # Exécuter la fonction
    result = search_web("test query")
    
    # Vérifier que l'erreur est retournée
    assert "Error searching for 'test query'" in result
    assert "API Error" in result
