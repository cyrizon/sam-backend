"""
Test pour vérifier la correction des erreurs de budget dans l'API
"""

import pytest
from unittest.mock import Mock, patch
from src.services.toll.route_optimization.toll_analysis.toll_selector import TollSelector
from src.cache.v2.models.toll_booth_station import TollBoothStation


def test_budget_api_fix():
    """Test pour reproduire et valider la correction des erreurs budget."""
    
    print("=" * 80)
    print("🔧 TEST CORRECTION ERREURS BUDGET API")
    print("=" * 80)
    
    # Créer des objets toll réalistes
    mock_toll_1 = Mock(spec=TollBoothStation)
    mock_toll_1.osm_id = 'node/123456'
    mock_toll_1.name = 'Péage Test 1'
    mock_toll_1.operator = 'APRR'
    mock_toll_1.coordinates = [3.5, 47.8]
    
    mock_toll_2 = Mock(spec=TollBoothStation)
    mock_toll_2.osm_id = 'node/789012'
    mock_toll_2.name = 'Péage Test 2'
    mock_toll_2.operator = 'APRR'
    mock_toll_2.coordinates = [5.3, 45.9]
    
    # Simulation d'un résultat d'identification
    identification_result = {
        'total_tolls_on_route': 2,
        'tolls_on_route': [
            {'toll': mock_toll_1, 'distance': 10.5, 'toll_type': 'fermé'},
            {'toll': mock_toll_2, 'distance': 20.3, 'toll_type': 'fermé'}
        ],
        'route_info': {
            'start_point': [3.0, 47.0],
            'end_point': [6.0, 46.0]
        }
    }
    
    toll_selector = TollSelector()
    
    # Test 1: Budget = 0 (cas qui générait l'erreur)
    print("\n1. 💸 TEST BUDGET = 0 (correction NoneType)")
    print("-" * 50)
    
    try:
        result_zero_budget = toll_selector.select_tolls_by_budget(
            identification_result['tolls_on_route'],
            target_budget=0.0,
            identification_result=identification_result
        )
        
        print("   ✅ Budget 0 traité sans erreur")
        print(f"   📋 Résultat: {result_zero_budget['selection_valid']}")
        print(f"   📊 Péages sélectionnés: {len(result_zero_budget['selected_tolls'])}")
        print(f"   💰 Coût: {result_zero_budget.get('total_cost', 'N/A')}€")
        
        assert result_zero_budget['selection_valid'] is True
        assert len(result_zero_budget['selected_tolls']) == 0  # Aucun péage avec budget 0
        
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
        raise
    
    # Test 2: Budget très petit (mais pas 0)
    print("\n2. 🪙 TEST BUDGET TRÈS PETIT")
    print("-" * 50)
    
    try:
        result_small_budget = toll_selector.select_tolls_by_budget(
            identification_result['tolls_on_route'],
            target_budget=1.0,
            identification_result=identification_result
        )
        
        print("   ✅ Petit budget traité sans erreur")
        print(f"   📋 Résultat: {result_small_budget['selection_valid']}")
        print(f"   📊 Péages sélectionnés: {len(result_small_budget['selected_tolls'])}")
        print(f"   💰 Coût: {result_small_budget.get('total_cost', 'N/A')}€")
        
        assert result_small_budget['selection_valid'] is True
        
        # Vérifier que seuls des objets sont retournés
        for i, toll in enumerate(result_small_budget['selected_tolls']):
            assert not isinstance(toll, dict), f"Péage {i+1} est un dict au lieu d'un objet"
            print(f"   📍 Péage {i+1}: {type(toll).__name__}")
            
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
        raise
    
    # Test 3: Budget normal
    print("\n3. 💰 TEST BUDGET NORMAL")
    print("-" * 50)
    
    # Mock le calcul de coût pour éviter les dépendances
    with patch('src.services.toll.route_optimization.utils.cache_accessor.CacheAccessor.calculate_toll_cost', return_value=8.50):
        try:
            result_normal_budget = toll_selector.select_tolls_by_budget(
                identification_result['tolls_on_route'],
                target_budget=20.0,
                identification_result=identification_result
            )
            
            print("   ✅ Budget normal traité sans erreur")
            print(f"   📋 Résultat: {result_normal_budget['selection_valid']}")
            print(f"   📊 Péages sélectionnés: {len(result_normal_budget['selected_tolls'])}")
            print(f"   💰 Coût: {result_normal_budget.get('total_cost', 'N/A')}€")
            
            assert result_normal_budget['selection_valid'] is True
            
            # Vérifier que seuls des objets sont retournés
            for i, toll in enumerate(result_normal_budget['selected_tolls']):
                assert not isinstance(toll, dict), f"Péage {i+1} est un dict au lieu d'un objet"
                print(f"   📍 Péage {i+1}: {type(toll).__name__}")
                
        except Exception as e:
            print(f"   ❌ ERREUR: {e}")
            raise
    
    # Test 4: Budget None (cas d'erreur)
    print("\n4. ❌ TEST BUDGET NONE")
    print("-" * 50)
    
    try:
        result_none_budget = toll_selector.select_tolls_by_budget(
            identification_result['tolls_on_route'],
            target_budget=None,
            identification_result=identification_result
        )
        
        print("   ✅ Budget None géré sans crash")
        print(f"   📋 Résultat: {result_none_budget['selection_valid']}")
        print(f"   📊 Péages sélectionnés: {len(result_none_budget['selected_tolls'])}")
        
        assert result_none_budget['selection_valid'] is True
        assert len(result_none_budget['selected_tolls']) == 0  # Route sans péage
        
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
        raise
    
    print("\n" + "=" * 80)
    print("🎉 TOUTES LES CORRECTIONS BUDGET VALIDÉES !")
    print("✅ Aucune erreur NoneType")
    print("✅ Aucune erreur d'argument manquant")
    print("✅ Gestion correcte des cas limites")
    print("✅ Objets exclusivement retournés")
    print("=" * 80)


if __name__ == "__main__":
    test_budget_api_fix()
    print("\n🏆 TEST CORRECTION BUDGET API RÉUSSI !")
