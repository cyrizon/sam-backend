from flask import Flask
from dotenv import load_dotenv
import os
from src.config.config import Config

def create_app():
    # Charger les variables d'environnement
    load_dotenv()

    # Créer l'application Flask
    app = Flask(__name__)

    # Charger la configuration en fonction de l'environnement
    env = os.getenv("FLASK_ENV", "dev")
    config = Config().dev_config if env == "dev" else Config().production_config
    app.config.from_object(config)

    print("🚀 Initialisation du cache global des péages...")
    from src.services.toll_data_cache import toll_data_cache
    toll_data_cache.initialize()

    # Enregistrer les routes
    from src.routes import register_routes
    register_routes(app)

    return app