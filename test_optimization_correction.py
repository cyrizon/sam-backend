"""
Test rapide pour vérifier la correction de l'optimisation des péages
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.toll.route_optimization.main.intelligent_optimizer import IntelligentOptimizer
from src.cache.v2.managers.v2_cache_manager_with_linking import V2CacheManagerWithLinking

def test_toll_optimization_correction():
    """Test que l'optimisation conserve bien les péages sélectionnés."""
    
    print("🧪 Test correction optimisation péages")
    
    # Utiliser des coordonnées réelles qui passent par des péages
    coordinates = [
        [7.448595, 48.262004],  # Strasbourg 
        [4.840823, 45.752181]   # Lyon
    ]
    
    # Mock ORS service simple
    class MockORS:
        def directions(self, coordinates, profile="driving-car", **kwargs):
            return {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": coordinates
                    },
                    "properties": {
                        "summary": {"distance": 500000, "duration": 18000},
                        "segments": [{
                            "distance": 500000,
                            "duration": 18000,
                            "steps": [{
                                "instruction": "Continue",
                                "name": "A35",
                                "distance": 500000,
                                "duration": 18000
                            }]
                        }]
                    }
                }]
            }
    
    # Initialiser l'optimiseur
    optimizer = IntelligentOptimizer(MockORS())
    
    # Test avec 2 péages demandés
    print("🎯 Test optimisation avec 2 péages demandés")
    result = optimizer.find_optimized_route(coordinates, target_tolls=2)
    
    if result:
        print(f"✅ Résultat obtenu:")
        print(f"   📊 Péages trouvés: {result.get('toll_count', 0)}")
        print(f"   💰 Coût: {result.get('cost', 0)}€")
        print(f"   🛣️ Distance: {result.get('distance', 0)/1000:.1f}km")
        print(f"   📍 Péages: {[toll.get('from_name', 'Inconnu') for toll in result.get('tolls', [])]}")
        
        # Vérifier que des péages ont été trouvés
        if result.get('toll_count', 0) > 0:
            print("✅ Test réussi - Des péages ont été conservés après optimisation")
            return True
        else:
            print("❌ Test échoué - Aucun péage trouvé après optimisation")
            return False
    else:
        print("❌ Test échoué - Aucun résultat")
        return False

if __name__ == "__main__":
    test_toll_optimization_correction()
