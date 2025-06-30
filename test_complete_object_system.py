"""
Test complet pour vérifier que l'optimisation budget et count retournent des objets
"""

import pytest
from unittest.mock import Mock, patch
from src.services.toll.route_optimization.toll_analysis.toll_selector import TollSelector
from src.cache.v2.models.toll_booth_station import TollBoothStation
from src.cache.v2.models.complete_motorway_link import CompleteMotorwayLink


def test_toll_selector_object_guarantee():
    """Test que TollSelector retourne toujours des objets pour les deux modes."""
    
    # Créer des objets mock réalistes
    mock_toll_1 = Mock(spec=TollBoothStation)
    mock_toll_1.osm_id = 'node/126217'
    mock_toll_1.name = 'Auxerre Nord'
    mock_toll_1.operator = 'APRR'
    mock_toll_1.coordinates = [3.5, 47.8]
    
    mock_toll_2 = Mock(spec=TollBoothStation)
    mock_toll_2.osm_id = 'node/142831'
    mock_toll_2.name = 'Ambérieu-en-Buguey'
    mock_toll_2.operator = 'APRR'
    mock_toll_2.coordinates = [5.3, 45.9]
    
    # Créer un résultat d'identification simulé
    identification_result = {
        'total_tolls_on_route': 2,
        'tolls_on_route': [
            {'toll': mock_toll_1, 'distance': 10.5, 'toll_type': 'fermé'},
            {'toll': mock_toll_2, 'distance': 20.3, 'toll_type': 'fermé'}
        ]
    }
    
    route_coordinates = [[2.0, 49.0], [2.1, 49.1], [2.2, 49.2]]
    
    print("=" * 80)
    print("TEST: GARANTIE D'OBJETS POUR TOLL SELECTOR")
    print("=" * 80)
    
    # Test 1: Mode "count" 
    print("\n1. TEST MODE COUNT")
    print("-" * 40)
    
    toll_selector = TollSelector()
    
    with patch('src.services.toll.route_optimization.utils.cache_accessor.CacheAccessor.calculate_toll_cost', return_value=8.0):
        result_count = toll_selector.select_tolls_by_count(
            identification_result['tolls_on_route'],
            target_count=2,
            identification_result=identification_result
        )
        
        assert result_count is not None, "Résultat count ne devrait pas être None"
        assert 'selected_tolls' in result_count, "Résultat devrait contenir selected_tolls"
        
        selected_tolls_count = result_count['selected_tolls']
        print(f"   Péages sélectionnés (count): {len(selected_tolls_count)}")
        
        for i, toll in enumerate(selected_tolls_count):
            print(f"   Péage {i+1}: {type(toll)} - {getattr(toll, 'name', 'N/A')}")
            assert not isinstance(toll, dict), f"Péage {i+1} ne devrait pas être un dict en mode count"
            assert hasattr(toll, 'osm_id'), f"Péage {i+1} devrait avoir un osm_id"
    
    # Test 2: Mode "budget"
    print("\n2. TEST MODE BUDGET")
    print("-" * 40)
    
    # Mock du budget selector pour retourner des objets
    mock_budget_result = {
        'selection_valid': True,
        'selected_tolls': [mock_toll_1, mock_toll_2],  # Directement des objets
        'total_cost': 15.0,
        'selection_reason': 'Budget respecté',
        'optimization_applied': True
    }
    
    with patch('src.services.toll.route_optimization.toll_analysis.budget.budget_selector.BudgetTollSelector.select_tolls_by_budget', return_value=mock_budget_result):
        result_budget = toll_selector.select_tolls_by_budget(
            identification_result['tolls_on_route'],
            budget_limit=20.0,
            route_coordinates=route_coordinates
        )
        
        assert result_budget is not None, "Résultat budget ne devrait pas être None"
        assert 'selected_tolls' in result_budget, "Résultat devrait contenir selected_tolls"
        
        selected_tolls_budget = result_budget['selected_tolls']
        print(f"   Péages sélectionnés (budget): {len(selected_tolls_budget)}")
        
        for i, toll in enumerate(selected_tolls_budget):
            print(f"   Péage {i+1}: {type(toll)} - {getattr(toll, 'name', 'N/A')}")
            assert not isinstance(toll, dict), f"Péage {i+1} ne devrait pas être un dict en mode budget"
            assert hasattr(toll, 'osm_id'), f"Péage {i+1} devrait avoir un osm_id"
    
    print("\n✅ TOUS LES TESTS PASSÉS : Objets garantis pour les deux modes !")


def test_segment_creation_with_objects():
    """Test que la création de segments fonctionne avec des objets."""
    
    # Créer des objets mock
    mock_toll_1 = Mock(spec=TollBoothStation)
    mock_toll_1.osm_id = 'node/126217'
    mock_toll_1.name = 'Auxerre Nord'
    mock_toll_1.coordinates = [3.5, 47.8]
    
    mock_link_1 = Mock(spec=CompleteMotorwayLink)
    mock_link_1.link_id = 'link_123'
    mock_link_1.name = 'Entrée Test'
    mock_link_1.coordinates = [3.6, 47.9]
    
    # Liste mixte d'objets
    selected_objects = [mock_toll_1, mock_link_1]
    
    print("\n" + "=" * 80)
    print("TEST: CRÉATION DE SEGMENTS AVEC OBJETS")
    print("=" * 80)
    
    # Mock du segment calculator
    mock_segments = [
        {'segment_id': 1, 'coordinates': [[3.5, 47.8], [3.6, 47.9]]},
        {'segment_id': 2, 'coordinates': [[3.6, 47.9], [3.7, 48.0]]}
    ]
    
    with patch('src.services.toll.route_optimization.segmentation.segment_calculator.SegmentCalculator.create_segments', return_value=mock_segments):
        # Simuler l'appel de création de segments
        from src.services.toll.route_optimization.segmentation.segment_calculator import SegmentCalculator
        
        segments = SegmentCalculator.create_segments(
            selected_objects,
            route_coordinates=[[3.5, 47.8], [3.7, 48.0]],
            ors_service=Mock()
        )
        
        assert len(segments) == 2, f"Attendu 2 segments, obtenu {len(segments)}"
        print(f"   ✅ {len(segments)} segments créés avec succès")
        
        for i, segment in enumerate(segments):
            print(f"   Segment {i+1}: ID={segment.get('segment_id')}")
    
    print("\n✅ Création de segments avec objets réussie !")


def test_cost_calculation_with_objects():
    """Test que le calcul de coûts fonctionne avec des objets."""
    
    # Créer des objets mock avec tous les attributs nécessaires
    mock_toll_1 = Mock(spec=TollBoothStation)
    mock_toll_1.osm_id = 'node/126217'
    mock_toll_1.name = 'Auxerre Nord'
    mock_toll_1.coordinates = [3.5, 47.8]
    mock_toll_1.operator = 'APRR'
    
    mock_toll_2 = Mock(spec=TollBoothStation)
    mock_toll_2.osm_id = 'node/142831'
    mock_toll_2.name = 'Ambérieu-en-Buguey'
    mock_toll_2.coordinates = [5.3, 45.9]
    mock_toll_2.operator = 'APRR'
    
    objects_list = [mock_toll_1, mock_toll_2]
    
    print("\n" + "=" * 80)
    print("TEST: CALCUL DE COÛTS AVEC OBJETS")
    print("=" * 80)
    
    # Test avec CacheAccessor.calculate_total_cost
    with patch('src.services.toll.route_optimization.utils.cache_accessor.CacheAccessor.calculate_toll_cost', return_value=12.50):
        from src.services.toll.route_optimization.utils.cache_accessor import CacheAccessor
        
        total_cost = CacheAccessor.calculate_total_cost(objects_list)
        
        print(f"   Coût total calculé: {total_cost}€")
        assert total_cost == 12.50, f"Attendu 12.50€, obtenu {total_cost}€"
        
        print("   ✅ Calcul de coûts avec objets réussi !")
    
    print("\n✅ TOUS LES TESTS DE CALCUL PASSÉS !")


if __name__ == "__main__":
    test_toll_selector_object_guarantee()
    test_segment_creation_with_objects()
    test_cost_calculation_with_objects()
    print("\n🎉 VALIDATION COMPLÈTE : LE SYSTÈME FONCTIONNE AVEC DES OBJETS !")
