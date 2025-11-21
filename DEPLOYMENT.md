# Guide de Déploiement Gratuit (24/7)

Votre bot a des besoins spécifiques :
1. **Playwright** (Nécessite un navigateur Chromium, donc lourd en RAM/CPU)
2. **Base de données SQLite** (Nécessite un disque persistant, sinon vous perdez vos tweets/stats à chaque redémarrage)
3. **Streamlit** (Interface Web)

Voici les meilleures options gratuites pour héberger ce projet :

## Option 1 : Hugging Face Spaces (Recommandé pour Streamlit)
Hugging Face offre un hébergement gratuit pour les démos ML, parfait pour Streamlit.

**Avantages** : Gratuit, supporte Docker (donc Playwright), interface facile.
**Inconvénients** : Le "Space" se met en veille après 48h d'inactivité (il faut le visiter pour le réveiller). Le disque n'est pas persistant par défaut (sauf si vous payez), mais on peut utiliser un Dataset pour sauvegarder la DB.

### Étapes :
1. Créez un compte sur [Hugging Face](https://huggingface.co/).
2. Créez un **New Space**.
3. Choisissez **Docker** comme SDK.
4. Uploadez tout votre dossier projet (avec le `Dockerfile` que j'ai créé).
5. Ajoutez vos variables d'environnement (API Keys) dans les "Settings" du Space.

## Option 2 : Render.com
**Avantages** : Très simple, supporte Docker.
**Inconvénients** : La version gratuite se met en veille après 15 min d'inactivité. Il faut payer (7$/mois) pour du 24/7 réel et un disque persistant.

## Option 3 : Oracle Cloud "Always Free" (Le vrai 24/7)
**Avantages** : VPS gratuit à vie (jusqu'à 4 CPU ARM, 24GB RAM). C'est une vraie machine virtuelle.
**Inconvénients** : Inscription parfois difficile (carte bancaire requise pour vérification), configuration manuelle (Linux).

---

## Ma recommandation : Hugging Face Spaces (Docker)
C'est le plus simple pour commencer sans payer.

1. Créez un fichier `.dockerignore` pour ne pas envoyer votre `.venv` ou `.env` local :
```
.venv
.env
__pycache__
*.pyc
.git
```

2. Pour la persistance des données (éviter de perdre la DB), l'idéal gratuit est de connecter votre bot à une base de données externe gratuite comme **Supabase** ou **Neon** (PostgreSQL), au lieu de SQLite.
   *Si vous gardez SQLite sur Hugging Face gratuit, la base de données sera réinitialisée à chaque redémarrage du Space.*
