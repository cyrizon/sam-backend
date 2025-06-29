"""
Test Toll Selector avec Selection Analyzer
==========================================

Test du nouveau système de sélection de péages avec analyse et optimisation.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.services.toll.route_optimization.toll_analysis.toll_selector import TollSelector


def create_test_data():
    """Crée des données de test."""
    
    # Péages de test (mix ouvert/fermé)
    tolls_on_route = [
        {
            'osm_id': '1001',
            'name': 'Péage A10 Orléans',
            'toll_type': 'ouvert',
            'coordinates': [1.9, 47.9],
            'estimated_cost': 2.50
        },
        {
            'osm_id': '1002', 
            'name': 'Péage A71 Vierzon',
            'toll_type': 'fermé',
            'coordinates': [2.1, 47.2],
            'estimated_cost': 4.20,
            'is_on_route': True
        },
        {
            'osm_id': '1003',
            'name': 'Péage A20 Châteauroux',
            'toll_type': 'ouvert',
            'coordinates': [1.7, 46.8],
            'estimated_cost': 3.10
        }
    ]
    
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


def test_selection_by_count():
    """Test la sélection par nombre avec analyse."""
    print("🧪 Test sélection par nombre avec analyse...")
    
    toll_selector = TollSelector()
    tolls_on_route, identification_result = create_test_data()
    
    # Test avec 2 péages
    result = toll_selector.select_tolls_by_count(
        tolls_on_route=tolls_on_route,
        target_count=2,
        identification_result=identification_result
    )
    
    print(f"✅ Résultat sélection:")
    print(f"   - Valid: {result.get('selection_valid')}")
    print(f"   - Count: {result.get('selection_count')}")
    print(f"   - Optimisation appliquée: {result.get('optimization_applied')}")
    print(f"   - Éléments optimisés: {result.get('elements_optimized', 0)}")
    
    # Vérifier la structure segments
    segments = result.get('segments', [])
    print(f"   - Segments créés: {len(segments)}")
    
    for i, segment in enumerate(segments):
        toll_status = 'avec péage' if segment.get('has_toll') else 'sans péage'
        reason = segment.get('segment_reason', 'N/A')
        print(f"     Segment {i+1}: {toll_status} - {reason}")
    
    return result


def test_selection_by_budget():
    """Test la sélection par budget."""
    print("\n🧪 Test sélection par budget...")
    
    toll_selector = TollSelector()
    tolls_on_route, identification_result = create_test_data()
    
    # Test avec budget de 5€
    result = toll_selector.select_tolls_by_budget(
        tolls_on_route=tolls_on_route,
        target_budget=5.0,
        identification_result=identification_result
    )
    
    print(f"✅ Résultat budget:")
    print(f"   - Valid: {result.get('selection_valid')}")
    print(f"   - Count: {result.get('selection_count')}")
    print(f"   - Coût total: {result.get('total_cost')}€")
    print(f"   - Budget utilisé: {result.get('budget_used')}")
    
    return result


def test_edge_cases():
    """Test des cas limites."""
    print("\n🧪 Test cas limites...")
    
    toll_selector = TollSelector()
    _, identification_result = create_test_data()
    
    # Test avec liste vide
    result_empty = toll_selector.select_tolls_by_count(
        tolls_on_route=[],
        target_count=1,
        identification_result=identification_result
    )
    print(f"   Liste vide: {result_empty.get('selection_valid')}")
    
    # Test avec 0 péage demandé
    tolls_on_route, _ = create_test_data()
    result_zero = toll_selector.select_tolls_by_count(
        tolls_on_route=tolls_on_route,
        target_count=0,
        identification_result=identification_result
    )
    print(f"   0 péage demandé: {result_zero.get('selection_valid')}")
    print(f"   Segments créés: {len(result_zero.get('segments', []))}")


def main():
    """Test principal."""
    print("=" * 60)
    print("🚧 Test Toll Selector avec Selection Analyzer")
    print("=" * 60)
    
    try:
        # Tests principaux
        test_selection_by_count()
        test_selection_by_budget()
        test_edge_cases()
        
        print("\n✅ Tous les tests terminés avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
