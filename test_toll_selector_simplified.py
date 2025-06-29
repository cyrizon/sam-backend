"""
Test Toll Selector Simplifié
============================

Test du nouveau système simplifié de sélection en 3 étapes.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.services.toll.route_optimization.toll_analysis.toll_selector import TollSelector


def create_simple_test_data():
    """Crée des données de test simples."""
    
    # 5 péages : 2 ouverts, 3 fermés
    tolls_on_route = [
        {
            'osm_id': '1001',
            'name': 'Péage Ouvert 1',
            'toll_type': 'ouvert',
            'coordinates': [2.0, 47.0],
        },
        {
            'osm_id': '1002', 
            'name': 'Péage Fermé 1',
            'toll_type': 'fermé',
            'coordinates': [2.1, 47.1],
        },
        {
            'osm_id': '1003',
            'name': 'Péage Fermé 2',
            'toll_type': 'fermé',
            'coordinates': [2.2, 47.2],
        },
        {
            'osm_id': '1004',
            'name': 'Péage Ouvert 2',
            'toll_type': 'ouvert',
            'coordinates': [2.3, 47.3],
        },
        {
            'osm_id': '1005',
            'name': 'Péage Fermé 3',
            'toll_type': 'fermé',
            'coordinates': [2.4, 47.4],
        }
    ]
    
    identification_result = {
        'route_info': {
            'start_point': [2.0, 47.0],  # Début
            'end_point': [2.5, 47.5]     # Fin
        }
    }
    
    return tolls_on_route, identification_result


def test_step1_removal():
    """Test de l'étape 1 : suppression pour respecter la demande."""
    print("🧪 Test Étape 1 : Suppression de péages...")
    
    toll_selector = TollSelector()
    tolls_on_route, _ = create_simple_test_data()
    
    # Test avec 3 péages demandés (on doit supprimer 2)
    result = toll_selector._remove_tolls_to_match_count(tolls_on_route, 3)
    
    print(f"   - Sélection valide: {result['selection_valid']}")
    print(f"   - Péages sélectionnés: {len(result['selected_tolls'])}")
    print(f"   - Péages supprimés: {len(result['removed_tolls'])}")
    
    # Vérifier qu'on supprime les fermés d'abord
    removed_types = [t['toll_type'] for t in result['removed_tolls']]
    print(f"   - Types supprimés: {removed_types}")
    
    return result


def test_isolated_closed_toll():
    """Test du cas péage fermé isolé."""
    print("\n🧪 Test Péage fermé isolé...")
    
    toll_selector = TollSelector()
    tolls_on_route, _ = create_simple_test_data()
    
    # Demander 1 seul péage → péage fermé isolé impossible
    result = toll_selector._remove_tolls_to_match_count(tolls_on_route, 1)
    
    print(f"   - Sélection valide: {result['selection_valid']}")
    print(f"   - Raison: {result['reason']}")
    
    return result


def test_full_process():
    """Test du processus complet en 3 étapes."""
    print("\n🧪 Test Processus complet...")
    
    toll_selector = TollSelector()
    tolls_on_route, identification_result = create_simple_test_data()
    
    # Test avec 3 péages
    result = toll_selector.select_tolls_by_count(
        tolls_on_route=tolls_on_route,
        target_count=3,
        identification_result=identification_result
    )
    
    print(f"   - Sélection valide: {result['selection_valid']}")
    print(f"   - Éléments sélectionnés: {len(result['selected_tolls'])}")
    print(f"   - Segments créés: {len(result.get('segments', []))}")
    print(f"   - Optimisation appliquée: {result.get('optimization_applied')}")
    
    # Détails des segments
    segments = result.get('segments', [])
    for i, seg in enumerate(segments):
        toll_status = 'avec péage' if seg.get('has_toll') else 'sans péage'
        print(f"     Segment {i+1}: {toll_status}")
    
    return result


def test_zero_tolls():
    """Test avec 0 péage demandé."""
    print("\n🧪 Test 0 péage demandé...")
    
    toll_selector = TollSelector()
    tolls_on_route, identification_result = create_simple_test_data()
    
    result = toll_selector.select_tolls_by_count(
        tolls_on_route=tolls_on_route,
        target_count=0,
        identification_result=identification_result
    )
    
    print(f"   - Sélection valide: {result['selection_valid']}")
    print(f"   - Éléments sélectionnés: {len(result['selected_tolls'])}")
    print(f"   - Segments: {len(result.get('segments', []))}")
    
    if result.get('segments'):
        segment = result['segments'][0]
        print(f"   - Segment unique: {'avec péage' if segment.get('has_toll') else 'sans péage'}")


def main():
    """Test principal."""
    print("=" * 50)
    print("🚧 Test Toll Selector Simplifié (3 Étapes)")
    print("=" * 50)
    
    try:
        # Tests des étapes individuelles
        test_step1_removal()
        test_isolated_closed_toll()
        
        # Test du processus complet
        test_full_process()
        test_zero_tolls()
        
        print("\n✅ Tous les tests terminés avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
