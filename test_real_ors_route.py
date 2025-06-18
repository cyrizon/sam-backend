"""
Test avec la vraie route ORS Sélestat-Besançon pour trouver la sortie 6.1
"""

import os
import sys
import json

# Ajouter le répertoire parent au path pour pouvoir importer les modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.services.toll.new_segmentation.intelligent_segmentation_strategy_v2 import IntelligentSegmentationStrategyV2
from src.services.toll_data_cache import toll_data_cache
from unittest.mock import MagicMock

def test_with_real_ors_route():
    """Test avec la vraie route ORS pour trouver la sortie 6.1."""
    print("=== Test avec Vraie Route ORS Sélestat-Besançon ===")
    
    # Initialiser le cache des données
    try:
        toll_data_cache.initialize()
        print("✅ Cache initialisé")
    except Exception as e:
        print(f"⚠️ Erreur initialisation cache : {e}")
    
    # Charger la vraie route depuis le fichier téléchargé
    route_file = "C:\\Users\\pecni\\Downloads\\ors-route_1750265443265.json"
    
    if not os.path.exists(route_file):
        print(f"❌ Fichier route introuvable : {route_file}")
        return False
    
    with open(route_file, 'r', encoding='utf-8') as f:
        real_route_data = json.load(f)
    
    print(f"✅ Route ORS chargée depuis {route_file}")
    
    # Coordonnées réelles Sélestat-Besançon
    coords_selestat_besancon = [[7.446851, 48.260845], [6.025151, 47.246151]]
    
    # Mock du service ORS qui retourne la vraie route
    mock_ors = MagicMock()
    
    def mock_get_route(coordinates, include_tollways=True):
        return real_route_data
    
    def mock_avoid_tollways(coordinates):
        # Route de contournement simplifiée
        return {
            "type": "FeatureCollection", 
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        coordinates[0],  # Point de départ
                        [6.5, 47.3],     # Détour sans péages
                        coordinates[1]   # Point d'arrivée
                    ]
                },
                "properties": {
                    "summary": {
                        "distance": 180000,   # 180 km
                        "duration": 6400      # 1h47min
                    }
                }
            }]
        }
    
    mock_ors.get_base_route.side_effect = mock_get_route
    mock_ors.get_route_avoid_tollways.side_effect = mock_avoid_tollways
    
    # Créer la stratégie avec le vrai fichier OSM
    strategy = IntelligentSegmentationStrategyV2(mock_ors, 'data/osm_export.geojson')
    
    print(f"\n🧠 Test de la stratégie avec 1 péage demandé...")
    print(f"📍 Recherche de la sortie 6.1 à [6.766417, 47.4650316]")
    
    try:
        result = strategy.find_route_with_exact_tolls(coords_selestat_besancon, 1)
        
        if result:
            print(f"✅ Résultat obtenu :")
            print(f"   Status : {result.get('status')}")
            print(f"   Péages utilisés : {result.get('actual_tolls')}")
            if 'used_tolls' in result:
                for toll in result['used_tolls']:
                    print(f"   - {toll['name']} ({toll['system']})")
            return True
        else:
            print(f"❌ Aucun résultat obtenu")
            return False
            
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_with_real_ors_route()
    if not success:
        sys.exit(1)
