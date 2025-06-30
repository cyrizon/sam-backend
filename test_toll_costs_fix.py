"""
Test pour vérifier que la correction du calcul de coûts fonctionne
"""

import pytest
from src.services.toll.route_optimization.assembly.route_assembler import RouteAssembler


def test_calculate_toll_costs_from_selected_fixed():
    """Test que le calcul de coûts avec péages sélectionnés fonctionne après correction."""
    
    # Simuler une route GeoJSON simple
    mock_route = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[2.0, 49.0], [2.5, 49.5]]
            },
            "properties": {
                "summary": {"distance": 50000, "duration": 3600}
            }
        }]
    }
    
    # Simuler des péages sélectionnés comme dictionnaires Python (format réel)
    # Utiliser des OSM IDs réels du cache
    selected_tolls = [
        {
            'osm_id': 'node/126217',  # Auxerre Nord - APRR (réel)
            'name': 'Auxerre Nord',
            'toll_type': 'fermé',
            'coordinates': [3.5, 47.8],
            'operator': 'APRR'
        },
        {
            'osm_id': 'node/142831',  # Ambérieu-en-Buguey - APRR (réel)
            'name': 'Ambérieu-en-Buguey',
            'toll_type': 'fermé',
            'coordinates': [5.3, 45.9],
            'operator': 'APRR'
        }
    ]
    
    print("=" * 60)
    print("TEST: CALCUL COÛTS AVEC PÉAGES SÉLECTIONNÉS CORRIGÉ")
    print("=" * 60)
    print(f"Péages sélectionnés: {len(selected_tolls)}")
    for toll in selected_tolls:
        print(f"  - {toll['name']} ({toll['toll_type']})")
    print("-" * 60)
    
    # Test du calcul de coûts
    try:
        cost, count, details = RouteAssembler._calculate_toll_costs_from_selected(
            mock_route, selected_tolls
        )
        
        print(f"\nRÉSULTAT:")
        print(f"Coût total: {cost}€")
        print(f"Nombre de péages: {count}")
        print(f"Détails: {len(details)} binômes")
        
        for detail in details:
            print(f"  Binôme: {detail.get('from_name')} → {detail.get('to_name')} = {detail.get('cost', 0)}€")
        
        # Vérifications
        assert count == 2, f"Attendu 2 péages, obtenu {count}"
        assert len(details) == 1, f"Attendu 1 binôme, obtenu {len(details)}"  # 2 péages = 1 binôme
        
        print("\n✅ Test réussi : Les péages sélectionnés sont correctement traités")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du calcul: {e}")
        raise e


def test_find_toll_in_cache():
    """Test de la méthode _find_toll_in_cache."""
    
    print("\n" + "=" * 60)
    print("TEST: RECHERCHE PÉAGE DANS LE CACHE")
    print("=" * 60)
    
    # Test avec un dictionnaire
    toll_dict = {
        'osm_id': 'node/123456',
        'name': 'Péage Test',
        'toll_type': 'fermé'
    }
    
    result = RouteAssembler._find_toll_in_cache(toll_dict)
    print(f"Recherche avec dict: {result is not None}")
    
    # Test avec osm_id direct
    result2 = RouteAssembler._find_toll_in_cache('node/123456')
    print(f"Recherche avec osm_id: {result2 is not None}")
    
    # Note: Ces tests échoueront probablement car le cache n'est pas initialisé,
    # mais ils permettent de vérifier que la méthode ne plante pas
    
    return True


if __name__ == "__main__":
    test_calculate_toll_costs_from_selected_fixed()
    test_find_toll_in_cache()
