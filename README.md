---
title: Twitter Bot News
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

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

## 📝 Changelog & Réalisations (Session Pair Programming)

Ce projet a été considérablement amélioré pour devenir un bot autonome, robuste et déployable gratuitement. Voici un résumé des travaux effectués :

### 🚀 Déploiement & Infrastructure
- **Dockerisation complète** : Création d'un `Dockerfile` optimisé pour Hugging Face Spaces (Python 3.11, Port 7860).
- **Stabilité du Background** : Implémentation de `worker.py` pour gérer le scheduler et éviter les crashs silencieux du conteneur.
- **Persistance des Données** : Système de sauvegarde des sujets de veille via la variable d'environnement `FIXED_TOPICS` (contourne le disque éphémère des Spaces).
- **Guide de Déploiement** : Documentation complète (`DEPLOYMENT.md`) pour héberger le bot gratuitement.

### 🤖 Fonctionnalités du Bot
- **Veille Automatique** : Scraper intelligent qui filtre les articles par date (moins d'une semaine) pour garantir la fraîcheur.
- **Génération IA** : Intégration de Gemini pour rédiger des tweets engageants avec choix du ton.
- **Support Twitter Premium** : Prise en charge des tweets longs (jusqu'à 25 000 caractères) et désactivation du threading automatique.
- **Gestion des Quotas** : Backoff exponentiel pour gérer les erreurs `429 Too Many Requests` de l'API Twitter.

### 🖥️ Interface de Gestion (Streamlit)
- **Dashboard** : Vue d'ensemble des tweets en attente et statistiques mensuelles.
- **Validation Manuelle** : File d'attente pour relire, modifier (texte/image) et valider chaque tweet avant envoi.
- **Outils de Debug** :
    - Bouton "Test Tweet (Sync)" pour vérifier la connexion API en direct.
    - Bouton "Force Run" pour lancer la veille manuellement.
    - Outil de rechargement des sujets persistants.

---

## 🔮 Roadmap / Pistes d'Évolution

Voici des idées pour aller encore plus loin avec ce projet :

### 1. Base de Données Robuste
- **Migration vers PostgreSQL/Supabase** : Actuellement sur SQLite (fichier local), la base se reset à chaque redémarrage du Space (sauf les `FIXED_TOPICS`). Passer sur une vraie DB cloud permettrait de conserver l'historique des tweets et les stats sur le long terme.

### 2. Intelligence Artificielle Avancée
- **RAG (Retrieval Augmented Generation)** : Donner au bot une "mémoire" de ses anciens tweets pour éviter les répétitions ou créer des fils conducteurs.
- **Analyse d'Images** : Utiliser Gemini Vision pour analyser les images des articles et générer des descriptions (Alt Text) automatiques pour l'accessibilité.

### 3. Multimédia & Engagement
- **Support Vidéo/GIF** : Permettre l'upload de vidéos natives ou la recherche de GIFs via Giphy.
- **Auto-Reply** : Un mode où le bot peut répondre automatiquement aux commentaires sous ses tweets (avec validation humaine optionnelle).

### 4. Multi-Compte
- Gérer plusieurs comptes Twitter depuis la même interface (ex: un compte Tech, un compte Crypto).

### 5. Notifications
- Recevoir une alerte (Discord, Telegram, Email) quand un nouveau tweet est prêt à être validé, pour ne pas avoir à vérifier l'interface en permanence.

