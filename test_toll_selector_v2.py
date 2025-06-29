"""
Test Toll Selector V2 avec Replacement Engine
=============================================

Tests du nouveau système de sélection de péages avec remplacement intelligent.
"""

import pytest
from unittest.mock import Mock, patch
from src.services.toll.route_optimization.toll_analysis.toll_selector import TollSelector


class TestTollSelectorV2:
    """Tests pour le nouveau TollSelector avec remplacement."""
    
    def setup_method(self):
        """Configuration des tests."""
        self.toll_selector = TollSelector()
        
        # Mock de données de test
        self.sample_route_coords = [
            [2.3522, 48.8566],  # Paris
            [2.3622, 48.8466],  # Point 2
            [2.3722, 48.8366],  # Point 3
            [2.3822, 48.8266]   # Point 4
        ]
        
        self.sample_tolls = [
            {
                'name': 'Péage Ouvert A1',
                'coordinates': [2.3522, 48.8566],
                'toll_type': 'ouvert',
                'operator': 'ASF'
            },
            {
                'name': 'Péage Fermé B1',
                'coordinates': [2.3622, 48.8466],
                'toll_type': 'fermé',
                'operator': 'APRR'
            },
            {
                'name': 'Péage Fermé C1',
                'coordinates': [2.3722, 48.8366],
                'toll_type': 'fermé',
                'operator': 'SANEF'
            },
            {
                'name': 'Péage Fermé D1',
                'coordinates': [2.3822, 48.8266],
                'toll_type': 'fermé',
                'operator': 'COFIROUTE'
            }
        ]
        
        self.sample_identification_result = {
            'total_tolls_on_route': len(self.sample_tolls),
            'tolls_on_route': self.sample_tolls,
            'route_coordinates': self.sample_route_coords
        }
    
    def test_toll_selector_initialization(self):
        """Test l'initialisation du sélecteur."""
        assert self.toll_selector.replacement_engine is not None
        print("✅ TollSelector initialisé avec replacement engine")
    
    @patch('src.services.toll.route_optimization.toll_analysis.toll_selector.CacheAccessor')
    def test_calculate_total_toll_cost(self, mock_cache):
        """Test le calcul du coût total des péages."""
        # Configuration du mock
        mock_cache.get_links_with_tolls.return_value = [Mock(has_toll=lambda: True)]
        mock_cache.calculate_toll_cost.return_value = 5.5
        
        total_cost = self.toll_selector._calculate_total_toll_cost(self.sample_tolls)
        
        assert total_cost > 0
        print(f"✅ Coût total calculé : {total_cost}€")
    
    def test_estimate_toll_cost(self):
        """Test l'estimation du coût d'un péage."""
        open_toll = {'toll_type': 'ouvert'}
        closed_toll = {'toll_type': 'fermé'}
        
        open_cost = self.toll_selector._estimate_toll_cost(open_toll)
        closed_cost = self.toll_selector._estimate_toll_cost(closed_toll)
        
        assert open_cost == 2.5
        assert closed_cost == 8.0
        print(f"✅ Coûts estimés : Ouvert {open_cost}€, Fermé {closed_cost}€")
    
    def test_convert_replacement_to_toll(self):
        """Test la conversion d'un remplacement en péage."""
        replacement_data = {
            'replacement_entry': {
                'toll_name': 'Entrée Test',
                'coordinates': [2.3522, 48.8566],
                'toll_type': 'ouvert',
                'operator': 'ASF'
            },
            'original_toll': {
                'name': 'Péage Original',
                'coordinates': [2.3622, 48.8466]
            },
            'replacement_score': 0.85
        }
        
        toll = self.toll_selector._convert_replacement_to_toll(replacement_data)
        
        assert toll['name'] == 'Entrée Test'
        assert toll['replacement'] == True
        assert toll['replacement_score'] == 0.85
        print("✅ Conversion remplacement vers péage")
    
    @patch('src.services.toll.route_optimization.toll_analysis.toll_selector.SingleTollSelector')
    def test_select_tolls_by_count_single_toll(self, mock_single_selector):
        """Test sélection d'un seul péage."""
        mock_single_selector.select_single_open_toll.return_value = {
            'selected_tolls': [self.sample_tolls[0]],
            'selection_valid': True
        }
        
        result = self.toll_selector.select_tolls_by_count(
            self.sample_tolls, 1, self.sample_identification_result
        )
        
        assert result['selection_valid'] == True
        mock_single_selector.select_single_open_toll.assert_called_once()
        print("✅ Sélection d'un seul péage")
    
    @patch('src.services.toll.route_optimization.toll_analysis.toll_selector.SelectionResultBuilder')
    def test_select_tolls_by_count_keep_all(self, mock_builder):
        """Test sélection de tous les péages."""
        mock_builder.create_selection_result.return_value = {
            'selected_tolls': self.sample_tolls,
            'selection_valid': True
        }
        
        result = self.toll_selector.select_tolls_by_count(
            self.sample_tolls, 10, self.sample_identification_result
        )
        
        mock_builder.create_selection_result.assert_called_once()
        print("✅ Sélection de tous les péages")
    
    @patch('src.services.toll.route_optimization.toll_analysis.toll_selector.CacheAccessor')
    def test_select_tolls_by_budget_sufficient(self, mock_cache):
        """Test sélection par budget suffisant."""
        mock_cache.is_cache_available.return_value = True
        
        result = self.toll_selector.select_tolls_by_budget(
            self.sample_tolls, 100.0, self.sample_identification_result
        )
        
        assert 'selected_tolls' in result
        print("✅ Sélection par budget suffisant")
    
    @patch('src.services.toll.route_optimization.toll_analysis.toll_selector.CacheAccessor')
    def test_select_tolls_by_budget_cache_unavailable(self, mock_cache):
        """Test sélection par budget avec cache indisponible."""
        mock_cache.is_cache_available.return_value = False
        
        result = self.toll_selector.select_tolls_by_budget(
            self.sample_tolls, 50.0, self.sample_identification_result
        )
        
        assert result['selection_valid'] == False
        print("✅ Gestion cache indisponible")


def test_replacement_engine_integration():
    """Test d'intégration avec le replacement engine."""
    toll_selector = TollSelector()
    
    # Vérifier que le replacement engine est bien initialisé
    assert hasattr(toll_selector, 'replacement_engine')
    assert toll_selector.replacement_engine is not None
    
    print("✅ Intégration Replacement Engine")


if __name__ == "__main__":
    # Tests rapides
    test_suite = TestTollSelectorV2()
    test_suite.setup_method()
    
    print("🧪 Tests TollSelector V2 avec Replacement Engine")
    print("=" * 50)
    
    test_suite.test_toll_selector_initialization()
    test_suite.test_estimate_toll_cost()
    test_suite.test_convert_replacement_to_toll()
    test_replacement_engine_integration()
    
    print("=" * 50)
    print("✅ Tests de base réussis !")
