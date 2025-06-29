"""
Test du Système Refactorisé
===========================

Test des modules refactorisés avec cache V2.
"""

from src.services.toll.route_optimization.toll_analysis.toll_identifier import TollIdentifier
from src.services.toll.route_optimization.toll_analysis.toll_selector import TollSelector


def test_refactored_system():
    """Test complet du système refactorisé."""
    print("🧪 Test du système route_optimization refactorisé...")
    
    # Test 1: TollIdentifier refactorisé
    print("\n1. Test TollIdentifier V2:")
    identifier = TollIdentifier()
    
    # Test identification sur route fictive
    route_coords = [[2.3522, 48.8566], [2.4522, 48.9566]]
    identification_result = identifier.identify_tolls_on_route(route_coords)
    
    print(f"   Identification réussie: {identification_result.get('identification_success')}")
    print(f"   Péages trouvés: {identification_result.get('total_tolls_on_route', 0)}")
    
    # Test 2: TollSelector refactorisé
    print("\n2. Test TollSelector V2:")
    selector = TollSelector()
    
    # Simuler des péages pour test
    mock_tolls = [
        {'name': 'Péage A', 'toll_type': 'ouvert', 'is_on_route': True},
        {'name': 'Péage B', 'toll_type': 'fermé', 'is_on_route': True},
        {'name': 'Péage C', 'toll_type': 'fermé', 'is_on_route': True}
    ]
    
    # Test sélection par nombre
    selection_result = selector.select_tolls_by_count(
        mock_tolls, 2, identification_result
    )
    
    print(f"   Sélection valide: {selection_result.get('selection_valid')}")
    print(f"   Péages sélectionnés: {selection_result.get('selection_count')}")
    print(f"   Raison: {selection_result.get('selection_reason')}")
    
    # Test 3: Statistiques des index spatiaux
    print("\n3. Test Index Spatiaux:")
    spatial_stats = identifier.get_spatial_index_stats()
    print(f"   Index prêts: {spatial_stats.get('all_indexes_ready')}")
    print(f"   Péages indexés: {spatial_stats.get('toll_index', {}).get('total_tolls', 0)}")
    print(f"   Entrées indexées: {spatial_stats.get('entry_index', {}).get('total_links', 0)}")
    
    print("\n✅ Test du système refactorisé terminé !")
    return True


if __name__ == "__main__":
    test_refactored_system()
