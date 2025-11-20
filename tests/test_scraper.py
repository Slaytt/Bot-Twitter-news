import pytest
from tools.scraper import scrape_website
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_scrape_website_success(mocker):
    """Test du scraping avec succès."""
    # Mock de async_playwright
    mock_playwright = mocker.patch("tools.scraper.async_playwright")
    
    # Configuration de la chaîne de mocks pour Playwright
    # async_playwright() -> context manager -> p
    mock_p = AsyncMock()
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_p
    mock_context.__aexit__.return_value = None
    mock_playwright.return_value = mock_context
    
    # p.chromium.launch() -> browser
    mock_browser = AsyncMock()
    mock_p.chromium.launch.return_value = mock_browser
    
    # browser.new_page() -> page
    mock_page = AsyncMock()
    mock_browser.new_page.return_value = mock_page
    
    # Configuration des retours de la page
    mock_page.inner_text.return_value = "Contenu de la page"
    mock_page.title.return_value = "Titre de la page"
    
    # Exécution
    url = "https://example.com"
    result = await scrape_website(url)
    
    # Vérifications
    assert "Title: Titre de la page" in result
    assert "Content:\nContenu de la page" in result
    
    # Vérifier les appels
    mock_page.goto.assert_called_once_with(url)
    mock_page.wait_for_load_state.assert_called_once_with("networkidle")
    mock_browser.close.assert_called_once()

@pytest.mark.asyncio
async def test_scrape_website_error(mocker):
    """Test de la gestion des erreurs lors du scraping."""
    # Mock pour lever une exception dès le début (ex: playwright fail)
    mock_playwright = mocker.patch("tools.scraper.async_playwright")
    mock_playwright.side_effect = Exception("Playwright Error")
    
    result = await scrape_website("https://example.com")
    
    assert "Error scraping https://example.com" in result
    assert "Playwright Error" in result
