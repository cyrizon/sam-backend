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

    print(" Initialisation du cache global OSM avec sérialisation...")
    from src.cache import osm_data_cache
    
    # Charger le cache OSM depuis le disque ou créer s'il n'existe pas
    # (Le cache des péages sera automatiquement initialisé si nécessaire)
    osm_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "osm_export_toll.geojson")
    success = osm_data_cache.load_osm_data_with_cache(osm_file_path)
    
    if success:
        print("✅ Cache OSM chargé avec succès")
    else:
        print("❌ Erreur lors du chargement du cache OSM")

    # Enregistrer les routes
    from src.routes import register_routes
    register_routes(app)

    return app