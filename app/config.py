"""Configuration centralisée — lue depuis les variables d'environnement.

Toute valeur de config DOIT passer par ce module. Ne jamais lire os.getenv()
directement ailleurs dans le code.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# === LLM Provider ===
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "")
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "Tempo Client")


# === Session cookie ===
SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-secret-change-in-production")
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "tempo_session")
SESSION_MAX_AGE = int(os.getenv("SESSION_MAX_AGE", "86400"))


# === Base de données ===
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/tempo.db")


# === ML Models ===
CHURN_MODEL_PATH = os.getenv("CHURN_MODEL_PATH", "./models/xgboost_churn.pkl")
RECO_MODEL_PATH = os.getenv("RECO_MODEL_PATH", "./models/reco_model.pkl")
SHAP_EXPLAINER_PATH = os.getenv("SHAP_EXPLAINER_PATH", "./models/shap_explainer.pkl")


# === Monitoring ===
EVIDENTLY_REPORTS_DIR = os.getenv("EVIDENTLY_REPORTS_DIR", "./data/evidently_reports")
LLM_COST_LOG_PATH = os.getenv("LLM_COST_LOG_PATH", "./data/llm_cost_log.jsonl")
DRIFT_CHECK_INTERVAL_HOURS = int(os.getenv("DRIFT_CHECK_INTERVAL_HOURS", "24"))


# === Scheduler ===
ALERT_CHECK_INTERVAL_MINUTES = int(os.getenv("ALERT_CHECK_INTERVAL_MINUTES", "60"))
TIMEZONE = os.getenv("TIMEZONE", "Europe/Paris")


# === Divers ===
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"


# === Utilisateurs en dur (démo uniquement) ===
# ATTENTION : en production réelle, ces users doivent être stockés en DB
# avec password hashé (bcrypt / argon2) et auth JWT ou OAuth2.
# Hashes bcrypt générés — passwords en clair :
#   conseiller_lille     -> "conseiller_lille2026"
#   conseiller_marseille -> "conseiller_marseille2026"
#   direction            -> "direction2026"
DEMO_USERS = {
    "conseiller_lille": {
        "password_hash": b'$2b$12$tAuIkelU6Xmh2eeAd6SUoOmnokm1yDZy0WJ7eQ/hyxZQggVSMgiLm',
        "role": "conseiller",
        "region": "lille",
        "nom_affiche": "Marie Dubois",
    },
    "conseiller_marseille": {
        "password_hash": b'$2b$12$fGG0yj3L.8o5maaztmwwSe8dvONgpBzTlUevttytj6E1Zd0yUy5Gi',
        "role": "conseiller",
        "region": "marseille",
        "nom_affiche": "Karim Benali",
    },
    "direction": {
        "password_hash": b'$2b$12$KGR7UA5li2KdbyKvNvvQqu5KNIgrbMtjlSNJWhKdrIqTgRnGUhClm',
        "role": "direction",
        "region": None,
        "nom_affiche": "Direction Marketing",
    },
}