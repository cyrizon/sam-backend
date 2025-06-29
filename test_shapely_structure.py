"""
Test spécifique avec la structure Shapely réelle.
"""

import sys
sys.path.append('.')

from src.services.toll.route_optimization.toll_analysis.selection_analyzer import SelectionAnalyzer
from src.cache.v2.models.toll_booth_station import TollBoothStation

def test_shapely_structure():
    """Test avec la vraie structure Shapely."""
    
    # Créer un TollBoothStation réel
    toll_station = TollBoothStation(
        osm_id='node/1707787330',
        name='Péage de Saint-Romain-de-Popey',
        operator='ASF',
        operator_ref='Péage de Saint-Romain-de-Popey',
        highway_ref='A 89',
        coordinates=[4.5087491, 45.872106],
        properties={},
        type='F'  # Fermé
    )
    
    # Structure exacte comme dans les logs
    toll_data_shapely = {
        'toll': toll_station,
        'shapely_distance': 0.002208981962794752,
        'source': 'optimized_on_route',
        'verification_method': 'shapely',
        'route_position': 0.7253896424090903
    }
    
    print("🧪 Test avec structure Shapely réelle")
    print(f"   Structure: {list(toll_data_shapely.keys())}")
    print(f"   TollStation: {toll_station.display_name}")
    print(f"   Type: {'fermé' if not toll_station.is_open_toll else 'ouvert'}")
    
    # Test de l'analyseur
    analyzer = SelectionAnalyzer()
    
    route_coords = [[7.448405, 48.261682], [3.11506, 45.784359]]
    
    print("\n🔧 Test optimisation...")
    result = analyzer._optimize_toll_element(toll_data_shapely, route_coords)
    
    print(f"\n📋 Résultat :")
    print(f"   Élément optimisé : {'✅ Trouvé' if result else '❌ Non trouvé'}")
    if result:
        print(f"   Type : {type(result).__name__}")
        if hasattr(result, 'display_name'):
            print(f"   Nom : {result.display_name}")

if __name__ == "__main__":
    test_shapely_structure()
