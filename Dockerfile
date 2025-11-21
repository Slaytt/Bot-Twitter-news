FROM python:3.10-slim

# Installation des dépendances système pour Playwright et autres outils
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Répertoire de travail
WORKDIR /app

# Copie des fichiers de dépendances
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Installation des navigateurs Playwright
RUN playwright install --with-deps chromium

# Copie du code source
COPY . .

# Variables d'environnement par défaut (à surcharger)
ENV PORT=8501

# Exposition du port Streamlit
EXPOSE 8501

# Commande de démarrage : lance le scheduler en arrière-plan et Streamlit au premier plan
# On utilise un script shell pour lancer les deux
RUN echo '#!/bin/bash\n\
python server.py & \n\
streamlit run interface.py --server.port=$PORT --server.address=0.0.0.0\n\
' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]
