"""Configuration de l'API.

Règle des 12 facteurs : toute la configuration vient des variables
d'environnement, jamais du code. En local, docker-compose les fournit ;
sur Kubernetes, ce seront un ConfigMap et un Secret.
"""
import os

# URL de connexion à la base de données (PostgreSQL en conteneur,
# SQLite en secours pour lancer l'API sans rien installer).
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# Redis est optionnel : si REDIS_HOST est vide, le cache est simplement désactivé.
REDIS_HOST = os.getenv("REDIS_HOST", "")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "30"))

# Version affichée par /api/info. Jenkins la remplacera plus tard
# par le hash court du commit déployé.
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
