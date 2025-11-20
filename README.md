# Serveur MCP Twitter Bot News

Ce projet implémente un serveur MCP (Model Context Protocol) en Python, fournissant des outils pour un bot Twitter automatisé, notamment un scraper web, une recherche web et la publication de tweets.

## Prérequis

- Python 3.10+
- `uv` (recommandé) ou `pip`
- Compte Twitter Developer (pour la publication de tweets)

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

4.  Configurer les credentials Twitter (optionnel) :
    ```bash
    cp .env.example .env
    # Éditer .env avec vos credentials Twitter
    ```

## Configuration Twitter

Pour utiliser la fonctionnalité de publication de tweets, vous devez obtenir des credentials d'API Twitter :

1. Créez un compte développeur sur [Twitter Developer Portal](https://developer.twitter.com/)
2. Créez une application et générez vos clés API
3. Ajoutez les credentials dans le fichier `.env` :
   ```
   TWITTER_API_KEY=votre_api_key
   TWITTER_API_SECRET=votre_api_secret
   TWITTER_ACCESS_TOKEN=votre_access_token
   TWITTER_ACCESS_TOKEN_SECRET=votre_access_token_secret
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

### Interface de test Streamlit

Une interface web Streamlit est disponible pour tester l'outil de scraping :

```bash
streamlit run interface.py
```

## Outils Disponibles

Le serveur MCP expose les outils suivants :

### `scrape(url: str) -> str`
Scrape le contenu textuel d'une page web en utilisant Playwright.
- **Paramètres** : `url` - L'URL de la page à scraper
- **Retour** : Le titre et le contenu textuel de la page

### `search_web(query: str, max_results: int = 5) -> str`
Effectue une recherche web via DuckDuckGo et retourne les résultats.
- **Paramètres** : 
  - `query` - La requête de recherche
  - `max_results` - Nombre maximum de résultats (défaut: 5)
- **Retour** : Liste formatée des résultats avec titres, URLs et descriptions

### `post_tweet(content: str) -> str`
Publie un tweet sur le compte Twitter configuré.
- **Paramètres** : `content` - Le contenu du tweet (max 280 caractères)
- **Retour** : L'ID du tweet publié ou un message d'erreur
- **Note** : Nécessite la configuration des credentials dans `.env`

## Architecture

```
Bot-Twitter-news/
├── server.py           # Serveur MCP principal
├── interface.py        # Interface Streamlit de test
├── test_scraper.py     # Script de test du scraper
├── requirements.txt    # Dépendances Python
├── .env.example        # Template de configuration
└── tools/              # Modules d'outils
    ├── scraper.py      # Outil de scraping Playwright
    ├── search.py       # Outil de recherche web
    └── twitter.py      # Outil de publication Twitter
```

## Prochaines étapes

- [ ] Planification automatique de tweets
- [ ] Génération de contenu avec IA
- [ ] Système de veille automatique sur des sujets

