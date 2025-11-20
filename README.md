# Serveur MCP Twitter Bot

Ce projet implémente un serveur MCP (Model Context Protocol) en Python, fournissant des outils pour un bot Twitter, notamment un scraper web basé sur Playwright.

## Prérequis

- Python 3.10+
- `uv` (recommandé) ou `pip`

## Installation

1.  Créer un environnement virtuel :
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Sur Windows: .venv\Scripts\activate
    ```

2.  Installer les dépendances :
    ```bash
    pip install -r requirements.txt
    ```

3.  Installer les navigateurs Playwright :
    ```bash
    playwright install chromium
    ```

## Utilisation

### Lancer le serveur MCP

Le serveur utilise `fastmcp` et communique via stdio.

```bash
python server.py
```

### Tester le scraper

Un script de test est fourni pour vérifier le fonctionnement de Playwright indépendamment de MCP :

```bash
python test_scraper.py
```

## Outils Disponibles

- `scrape(url: str) -> str`: Scrape le contenu textuel d'une page web.
