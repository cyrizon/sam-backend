"""
Test Logic - Intelligent Optimizer
=================================

Test de la logique des cas spéciaux de l'optimiseur intelligent.
"""

import pytest
from unittest.mock import Mock, MagicMock


def test_special_case_one_toll_only_closed():
    """
    Test du cas spécial : 1 péage demandé mais que des fermés sur la route.
    Doit renvoyer une route sans péage (car fermé isolé interdit).
    """
    # Mock de l'optimiseur
    from src.services.toll.route_optimization.main.intelligent_optimizer import IntelligentOptimizer
    
    # Mock du service ORS
    mock_ors = Mock()
    optimizer = IntelligentOptimizer(mock_ors)
    
    # Mock des données d'identification avec que des fermés
    identification_result = {
        'total_tolls_on_route': 3,
        'tolls_on_route': [
            {'toll_type': 'fermé', 'name': 'Fermé1'},
            {'toll_type': 'fermé', 'name': 'Fermé2'},  
            {'toll_type': 'fermé', 'name': 'Fermé3'}
        ]
    }
    
    # Test du cas spécial
    result = optimizer._is_base_route_sufficient(
        identification_result, 
        target_tolls=1, 
        optimization_mode='count'
    )
    
    # Doit retourner True pour forcer une route sans péage
    assert result == True
    print("✅ Cas spécial validé : 1 péage demandé + que des fermés → route sans péage")


def test_normal_case_one_toll_with_open():
    """
    Test du cas normal : 1 péage demandé avec des ouverts disponibles.
    Doit continuer l'optimisation normale.
    """
    from src.services.toll.route_optimization.main.intelligent_optimizer import IntelligentOptimizer
    
    # Mock du service ORS
    mock_ors = Mock()
    optimizer = IntelligentOptimizer(mock_ors)
    
    # Mock des données d'identification avec ouverts et fermés
    identification_result = {
        'total_tolls_on_route': 3,
        'tolls_on_route': [
            {'toll_type': 'ouvert', 'name': 'Ouvert1'},
            {'toll_type': 'fermé', 'name': 'Fermé1'},  
            {'toll_type': 'fermé', 'name': 'Fermé2'}
        ]
    }
    
    # Test du cas normal
    result = optimizer._is_base_route_sufficient(
        identification_result, 
        target_tolls=1, 
        optimization_mode='count'
    )
    
    # Doit retourner False pour continuer l'optimisation
    assert result == False
    print("✅ Cas normal validé : 1 péage demandé + ouverts disponibles → optimisation")


def test_multiple_tolls_case():
    """
    Test du cas : plusieurs péages demandés.
    Doit continuer l'optimisation même avec que des fermés.
    """
    from src.services.toll.route_optimization.main.intelligent_optimizer import IntelligentOptimizer
    
    # Mock du service ORS
    mock_ors = Mock()
    optimizer = IntelligentOptimizer(mock_ors)
    
    # Mock des données d'identification avec que des fermés
    identification_result = {
        'total_tolls_on_route': 4,
        'tolls_on_route': [
            {'toll_type': 'fermé', 'name': 'Fermé1'},
            {'toll_type': 'fermé', 'name': 'Fermé2'},
            {'toll_type': 'fermé', 'name': 'Fermé3'},
            {'toll_type': 'fermé', 'name': 'Fermé4'}
        ]
    }
    
    # Test avec 2 péages demandés
    result = optimizer._is_base_route_sufficient(
        identification_result, 
        target_tolls=2, 
        optimization_mode='count'
    )
    
    # Doit retourner False pour continuer l'optimisation
    assert result == False
    print("✅ Cas multiple validé : 2 péages demandés + fermés → optimisation possible")


if __name__ == "__main__":
    print("🧪 Test de la logique des cas spéciaux...")
    
    test_special_case_one_toll_only_closed()
    test_normal_case_one_toll_with_open()
    test_multiple_tolls_case()
    
    print("\n✅ Tous les tests de logique passent !")
