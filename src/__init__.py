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

    print("🚀 Initialisation du cache V2 complet avec linking...")
    from src.cache.managers.cache_manager_with_linking import CacheManagerWithLinking
    
    # Initialiser le cache V2 avec le répertoire des données
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    data_dir = os.path.abspath(data_dir)
    
    # Initialiser le cache V2 uniquement
    cache_v2 = CacheManagerWithLinking(data_dir)
    success = cache_v2.load_all_including_motorway_linking()
    
    if success:
        print("✅ Cache V2 complet avec linking chargé avec succès")
        print(f"📊 Statistiques:")
        print(f"   - Total toll booths: {len(cache_v2.toll_booths)}")
        
        # Calculer les stats
        open_tolls = len([t for t in cache_v2.toll_booths if t.is_open_toll])
        closed_tolls = len([t for t in cache_v2.toll_booths if t.is_closed_toll])
        
        print(f"   - Péages ouverts: {open_tolls}")
        print(f"   - Péages fermés: {closed_tolls}")
        print(f"   - Opérateurs disponibles: {len(cache_v2.pricing_manager.get_available_operators())}")
        print(f"   - Liens complets: {len(cache_v2.complete_motorway_links)}")
        
        # Stocker le cache globalement pour l'application
        app.config['CACHE_V2'] = cache_v2
        
    else:
        print("❌ Erreur critique lors du chargement du cache V2")
        raise RuntimeError("Impossible de charger le cache V2. Vérifiez les fichiers de données.")

    # Enregistrer les routes
    from src.routes import register_routes
    register_routes(app)

    return app