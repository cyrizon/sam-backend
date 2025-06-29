"""
Test Toll Selector avec vrais données
=====================================

Test du nouveau système de sélection avec les données réelles du cache.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.services.toll.route_optimization.toll_analysis.toll_selector import TollSelector
from src.cache.v2.managers.v2_cache_manager_with_pricing import V2CacheManagerWithPricing


def create_real_test_data():
    """Crée des données de test basées sur le vrai cache."""
    
    # Charger le cache pour récupérer des péages réels
    current_dir = os.path.dirname(__file__)
    data_dir = os.path.join(current_dir, 'data')
    data_dir = os.path.abspath(data_dir)
    
    cache_manager = V2CacheManagerWithPricing(data_dir)
    cache_manager.load_all()
    
    # Prendre quelques péages réels du cache
    real_tolls = cache_manager.toll_booths[:5]  # Les 5 premiers
    
    # Convertir en format de test
    tolls_on_route = []
    for toll in real_tolls:
        toll_data = {
            'osm_id': toll.osm_id,
            'name': toll.name or f"Péage {toll.osm_id}",
            'toll_type': 'ouvert' if toll.is_open_toll else 'fermé',
            'coordinates': toll.get_coordinates(),
            'estimated_cost': 3.50,  # Coût estimé pour test
            'is_on_route': True
        }
        tolls_on_route.append(toll_data)
    
    # Résultat d'identification simulé
    identification_result = {
        'route_info': {
            'start_point': [2.3522, 48.8566],  # Paris
            'end_point': [1.4442, 43.6043]      # Toulouse
        },
        'route_coordinates': [[2.3522, 48.8566], [1.4442, 43.6043]],
        'total_distance_km': 678.2
    }
    
    return tolls_on_route, identification_result


def test_with_real_data():
    """Test avec des données réelles du cache."""
    print("🧪 Test sélection avec données réelles...")
    
    tolls_on_route, identification_result = create_real_test_data()
    
    print(f"   📊 Péages récupérés du cache : {len(tolls_on_route)}")
    for i, toll in enumerate(tolls_on_route):
        print(f"     {i+1}. {toll['name']} ({toll['toll_type']}) à {toll['coordinates']}")
    
    toll_selector = TollSelector()
    
    # Test avec 3 péages
    result = toll_selector.select_tolls_by_count(
        tolls_on_route=tolls_on_route,
        target_count=3,
        identification_result=identification_result
    )
    
    print(f"\n✅ Résultat sélection :")
    print(f"   - Valid: {result.get('selection_valid')}")
    print(f"   - Count: {result.get('selection_count')}")
    print(f"   - Optimisation appliquée: {result.get('optimization_applied')}")
    print(f"   - Éléments optimisés: {result.get('elements_optimized', 0)}")
    
    # Détails des éléments sélectionnés
    selected_tolls = result.get('selected_tolls', [])
    print(f"   - Éléments sélectionnés: {len(selected_tolls)}")
    for i, toll in enumerate(selected_tolls):
        if hasattr(toll, 'osm_id'):
            print(f"     {i+1}. TollBoothStation: {toll.osm_id} - {getattr(toll, 'name', 'Inconnu')}")
        elif hasattr(toll, 'link_id'):
            print(f"     {i+1}. CompleteMotorwayLink: {toll.link_id}")
        else:
            print(f"     {i+1}. Autre: {type(toll)}")
    
    # Vérifier la structure segments
    segments = result.get('segments', [])
    print(f"   - Segments créés: {len(segments)}")
    
    for i, segment in enumerate(segments):
        toll_status = 'avec péage' if segment.get('has_toll') else 'sans péage'
        reason = segment.get('segment_reason', 'N/A')
        start = segment.get('start_point', [0, 0])
        end = segment.get('end_point', [0, 0])
        print(f"     Segment {i+1}: {toll_status}")
        print(f"       Start: [{start[0]:.4f}, {start[1]:.4f}]")
        print(f"       End: [{end[0]:.4f}, {end[1]:.4f}]")
        print(f"       Raison: {reason}")
    
    return result


def test_edge_case_no_tolls():
    """Test cas limite sans péages."""
    print("\n🧪 Test cas sans péages...")
    
    toll_selector = TollSelector()
    _, identification_result = create_real_test_data()
    
    result = toll_selector.select_tolls_by_count(
        tolls_on_route=[],
        target_count=2,
        identification_result=identification_result
    )
    
    print(f"   - Valid: {result.get('selection_valid')}")
    print(f"   - Segments: {len(result.get('segments', []))}")
    
    if result.get('segments'):
        segment = result['segments'][0]
        toll_status = 'avec péage' if segment.get('has_toll') else 'sans péage'
        print(f"   - Segment unique: {toll_status}")


def main():
    """Test principal."""
    print("=" * 60)
    print("🚧 Test Toll Selector avec Données Réelles")
    print("=" * 60)
    
    try:
        # Tests principaux
        test_with_real_data()
        test_edge_case_no_tolls()
        
        print("\n✅ Tous les tests terminés avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
