"""
Test pour vérifier le calcul de coût dans _is_base_route_sufficient
"""

import pytest
from unittest.mock import Mock, patch
from src.services.toll.route_optimization.main.intelligent_optimizer import IntelligentOptimizer


def test_budget_optimization_cost_calculation():
    """Test du calcul de coût pour l'optimisation par budget."""
    
    # Mock du service ORS
    mock_ors = Mock()
    optimizer = IntelligentOptimizer(mock_ors)
    
    # Simuler un résultat d'identification avec 2 péages
    identification_result = {
        'total_tolls_on_route': 2,
        'tolls_on_route': [
            {
                'toll': Mock(
                    osm_id='node/123456',
                    name='Péage A',
                    operator='VINCI',
                    coordinates=[2.0, 49.0]
                )
            },
            {
                'toll': Mock(
                    osm_id='node/789012', 
                    name='Péage B',
                    operator='VINCI',
                    coordinates=[2.1, 49.1]
                )
            }
        ]
    }
    
    print("=" * 60)
    print("TEST: CALCUL DE COÛT POUR OPTIMISATION BUDGET")
    print("=" * 60)
    
    # Test 1: Budget suffisant
    print("\n1. Test budget suffisant (15€)")
    with patch('src.services.toll.route_optimization.utils.cache_accessor.CacheAccessor.calculate_toll_cost', return_value=8.50):
        result = optimizer._is_base_route_sufficient(
            identification_result, 15.0, 'budget'
        )
        print(f"   Résultat: {result} (attendu: True)")
        assert result == True, "Budget suffisant devrait retourner True"
    
    # Test 2: Budget insuffisant  
    print("\n2. Test budget insuffisant (5€)")
    with patch('src.services.toll.route_optimization.utils.cache_accessor.CacheAccessor.calculate_toll_cost', return_value=8.50):
        result = optimizer._is_base_route_sufficient(
            identification_result, 5.0, 'budget'
        )
        print(f"   Résultat: {result} (attendu: False)")
        assert result == False, "Budget insuffisant devrait retourner False"
    
    # Test 3: Aucun péage
    print("\n3. Test aucun péage")
    empty_identification = {
        'total_tolls_on_route': 0,
        'tolls_on_route': []
    }
    result = optimizer._is_base_route_sufficient(
        empty_identification, 10.0, 'budget'
    )
    print(f"   Résultat: {result} (attendu: True)")
    assert result == True, "Aucun péage devrait retourner True"
    
    print("\n✅ Tous les tests passés !")


def test_calculate_route_cost_method():
    """Test de la méthode _calculate_route_cost directement."""
    
    mock_ors = Mock()
    optimizer = IntelligentOptimizer(mock_ors)
    
    # Péages de test
    tolls_on_route = [
        {
            'toll': Mock(
                osm_id='node/123456',
                name='Péage A',
                operator='VINCI',
                coordinates=[2.0, 49.0]
            )
        },
        {
            'toll': Mock(
                osm_id='node/789012',
                name='Péage B', 
                operator='VINCI',
                coordinates=[2.1, 49.1]
            )
        }
    ]
    
    print("\n" + "=" * 60)
    print("TEST: MÉTHODE _calculate_route_cost")
    print("=" * 60)
    
    # Mock du calcul de coût
    with patch('src.services.toll.route_optimization.utils.cache_accessor.CacheAccessor.calculate_toll_cost', return_value=8.50):
        cost = optimizer._calculate_route_cost(tolls_on_route)
        print(f"Coût calculé: {cost}€")
        assert cost == 8.50, f"Coût attendu: 8.50€, obtenu: {cost}€"
    
    # Test avec aucun péage
    cost_empty = optimizer._calculate_route_cost([])
    print(f"Coût pour aucun péage: {cost_empty}€")
    assert cost_empty == 0.0, "Coût devrait être 0 pour aucun péage"
    
    # Test avec un seul péage
    single_toll = [tolls_on_route[0]]
    cost_single = optimizer._calculate_route_cost(single_toll)
    print(f"Coût pour un seul péage: {cost_single}€")
    assert cost_single == 0.0, "Coût devrait être 0 pour un seul péage"
    
    print("\n✅ Tests de _calculate_route_cost passés !")


if __name__ == "__main__":
    test_budget_optimization_cost_calculation()
    test_calculate_route_cost_method()
