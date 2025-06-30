"""
Test pour vérifier que le BudgetSelector retourne toujours des objets et jamais des dictionnaires
"""

import pytest
from unittest.mock import Mock, patch
from src.services.toll.route_optimization.toll_analysis.budget.budget_selector import BudgetTollSelector
from src.cache.v2.models.toll_booth_station import TollBoothStation
from src.cache.v2.models.complete_motorway_link import CompleteMotorwayLink


def test_budget_selector_returns_only_objects():
    """Test que le BudgetSelector retourne toujours des objets, jamais des dicts."""
    
    # Créer un sélecteur
    selector = BudgetTollSelector()
    
    # Créer des péages de test (mélange de dicts et objets)
    mock_toll_station_1 = Mock(spec=TollBoothStation)
    mock_toll_station_1.osm_id = 'node/123456'
    mock_toll_station_1.name = 'Péage A'
    mock_toll_station_1.operator = 'VINCI'
    
    mock_toll_station_2 = Mock(spec=TollBoothStation)
    mock_toll_station_2.osm_id = 'node/789012'
    mock_toll_station_2.name = 'Péage B'
    mock_toll_station_2.operator = 'VINCI'
    
    # Péages sous forme de dictionnaires avec objets intégrés
    tolls_on_route = [
        {
            'toll': mock_toll_station_1,
            'distance': 10.5,
            'toll_type': 'ouvert'
        },
        {
            'toll': mock_toll_station_2,
            'distance': 20.3,
            'toll_type': 'ouvert'
        }
    ]
    
    print("=" * 60)
    print("TEST: BUDGET SELECTOR - GARANTIE D'OBJETS")
    print("=" * 60)
    
    # Test 1: Budget suffisant - tous les péages gardés
    print("\n1. Test budget suffisant")
    with patch('src.services.toll.route_optimization.utils.cache_accessor.CacheAccessor.calculate_toll_cost', return_value=5.0):
        result = selector.select_tolls_by_budget(
            tolls_on_route, 
            budget_limit=15.0,
            route_coordinates=[[2.0, 49.0], [2.1, 49.1]]
        )
        
        assert result is not None, "Résultat ne devrait pas être None"
        assert result['selection_valid'] is True, "Sélection devrait être valide"
        
        selected_tolls = result['selected_tolls']
        print(f"   Nombre de péages sélectionnés: {len(selected_tolls)}")
        
        # Vérifier que tous les éléments sont des objets
        for i, toll in enumerate(selected_tolls):
            print(f"   Péage {i+1}: {type(toll)} - {toll}")
            assert not isinstance(toll, dict), f"Péage {i+1} ne devrait pas être un dict: {type(toll)}"
            assert hasattr(toll, 'osm_id'), f"Péage {i+1} devrait avoir un attribut osm_id"
            assert hasattr(toll, 'name'), f"Péage {i+1} devrait avoir un attribut name"
    
    # Test 2: Budget insuffisant - route sans péage
    print("\n2. Test budget insuffisant")
    with patch('src.services.toll.route_optimization.utils.cache_accessor.CacheAccessor.calculate_toll_cost', return_value=10.0):
        result = selector.select_tolls_by_budget(
            tolls_on_route,
            budget_limit=5.0,
            route_coordinates=[[2.0, 49.0], [2.1, 49.1]]
        )
        
        assert result is not None, "Résultat ne devrait pas être None"
        selected_tolls = result['selected_tolls']
        print(f"   Nombre de péages sélectionnés: {len(selected_tolls)}")
        
        # Même si c'est une liste vide, vérifier qu'il n'y a pas de dicts
        for i, toll in enumerate(selected_tolls):
            assert not isinstance(toll, dict), f"Péage {i+1} ne devrait pas être un dict: {type(toll)}"
    
    print("\n✅ Test réussi : Aucun dictionnaire retourné !")


def test_convert_tolls_to_objects_method():
    """Test de la méthode _convert_tolls_to_objects."""
    
    selector = BudgetTollSelector()
    
    # Créer des objets mock
    mock_toll_station = Mock(spec=TollBoothStation)
    mock_toll_station.osm_id = 'node/123456'
    mock_toll_station.name = 'Péage Test'
    
    mock_motorway_link = Mock(spec=CompleteMotorwayLink)
    mock_motorway_link.link_id = 'link_123'
    mock_motorway_link.name = 'Entrée Test'
    
    # Test avec différents types d'entrées
    test_tolls = [
        # Dict avec objet intégré
        {'toll': mock_toll_station, 'distance': 10.5},
        # Objet direct
        mock_motorway_link,
        # Dict pur (sera cherché dans le cache)
        {'osm_id': 'node/999999', 'name': 'Péage Cache'}
    ]
    
    print("\n" + "=" * 60)
    print("TEST: MÉTHODE _convert_tolls_to_objects")
    print("=" * 60)
    
    # Mock de la recherche dans le cache
    with patch.object(selector, '_find_toll_station_in_cache', return_value=mock_toll_station):
        converted = selector._convert_tolls_to_objects(test_tolls)
        
        print(f"Nombre d'objets convertis: {len(converted)}")
        
        for i, toll in enumerate(converted):
            print(f"   Objet {i+1}: {type(toll)}")
            assert not isinstance(toll, dict), f"L'objet {i+1} ne devrait pas être un dict"
            # Vérifier que c'est bien un objet avec des attributs
            assert hasattr(toll, 'osm_id') or hasattr(toll, 'link_id'), \
                f"L'objet {i+1} devrait avoir des attributs d'identification"
    
    print("\n✅ Conversion en objets réussie !")


def test_budget_optimization_with_objects():
    """Test complet d'optimisation budget avec garantie d'objets."""
    
    selector = BudgetTollSelector()
    
    # Créer des péages fermés et ouverts
    mock_open_toll = Mock(spec=TollBoothStation)
    mock_open_toll.osm_id = 'node/111111'
    mock_open_toll.name = 'Péage Ouvert'
    
    mock_closed_toll = Mock(spec=TollBoothStation)
    mock_closed_toll.osm_id = 'node/222222'
    mock_closed_toll.name = 'Péage Fermé'
    
    tolls_mixed = [
        {'toll': mock_open_toll, 'toll_type': 'ouvert'},
        {'toll': mock_closed_toll, 'toll_type': 'fermé'}
    ]
    
    print("\n" + "=" * 60)
    print("TEST: OPTIMISATION BUDGET AVEC OBJETS")
    print("=" * 60)
    
    # Mock l'optimiseur pour retourner seulement les péages ouverts
    mock_optimizer_result = {
        'selection_valid': True,
        'selected_tolls': [mock_open_toll],  # Directement des objets
        'total_cost': 5.0,
        'selection_reason': 'Optimisé par budget',
        'optimization_applied': True
    }
    
    with patch.object(selector.optimizer, 'optimize_for_budget', return_value=mock_optimizer_result):
        with patch('src.services.toll.route_optimization.utils.cache_accessor.CacheAccessor.calculate_toll_cost', return_value=8.0):
            result = selector.select_tolls_by_budget(
                tolls_mixed,
                budget_limit=10.0,
                route_coordinates=[[2.0, 49.0], [2.1, 49.1]]
            )
            
            assert result is not None, "Résultat d'optimisation ne devrait pas être None"
            selected_tolls = result['selected_tolls']
            
            print(f"Péages après optimisation: {len(selected_tolls)}")
            
            for i, toll in enumerate(selected_tolls):
                print(f"   Péage {i+1}: {type(toll)}")
                assert not isinstance(toll, dict), \
                    f"Péage optimisé {i+1} ne devrait pas être un dict"
                assert hasattr(toll, 'osm_id'), \
                    f"Péage optimisé {i+1} devrait avoir un osm_id"
    
    print("\n✅ Optimisation avec objets réussie !")


if __name__ == "__main__":
    test_budget_selector_returns_only_objects()
    test_convert_tolls_to_objects_method()
    test_budget_optimization_with_objects()
    print("\n🎉 TOUS LES TESTS DE GARANTIE D'OBJETS PASSÉS !")
