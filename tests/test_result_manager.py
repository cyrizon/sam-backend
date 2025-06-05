"""
Tests pour RouteResultManager - Gestion des résultats d'optimisation.
"""
import pytest
from src.services.toll.result_manager import RouteResultManager
from src.services.toll.constants import TollOptimizationConfig as Config


class TestRouteResultManager:
    """Tests pour la gestion des résultats."""
    
    def test_initialization(self):
        """Test initialisation du gestionnaire."""
        manager = RouteResultManager()
        
        assert manager.best_fast["route"] is None
        assert manager.best_cheap["route"] is None
        assert manager.best_min_tolls["route"] is None
        assert manager.best_fast["cost"] == float('inf')
    
    def test_reset(self):
        """Test remise à zéro."""
        manager = RouteResultManager()
        
        # Simuler des données
        manager.best_fast = {"route": "fake", "cost": 10}
        
        manager.reset()
        
        assert manager.best_fast["route"] is None
        assert manager.best_fast["cost"] == float('inf')
    
    def test_initialize_with_base_route_valid(self):
        """Test initialisation avec route de base valide."""
        manager = RouteResultManager()
        base_route = {"features": [{"mock": "route"}]}
        
        manager.initialize_with_base_route(
            base_route=base_route,
            base_cost=10.5,
            base_duration=3600,
            base_toll_count=2,
            max_tolls=3
        )
        
        # Route de base respecte la contrainte (2 <= 3)
        assert manager.best_fast["route"] == base_route
        assert manager.best_fast["cost"] == 10.5
        assert manager.best_cheap["route"] == base_route
        assert manager.best_min_tolls["route"] == base_route
    
    def test_initialize_with_base_route_invalid(self):
        """Test initialisation avec route de base invalide."""
        manager = RouteResultManager()
        base_route = {"features": [{"mock": "route"}]}
        
        manager.initialize_with_base_route(
            base_route=base_route,
            base_cost=10.5,
            base_duration=3600,
            base_toll_count=4,  # Trop de péages
            max_tolls=3
        )
        
        # Route de base ne respecte pas la contrainte (4 > 3)
        assert manager.best_fast["route"] is None
        assert manager.best_cheap["route"] is None
        assert manager.best_min_tolls["route"] is None
    
    def test_update_with_route_cheapest(self):
        """Test mise à jour avec route moins chère."""
        manager = RouteResultManager()
        manager.best_cheap = {"route": "old", "cost": 15, "duration": 3000, "toll_count": 2}
        
        new_route = {
            "route": "new",
            "cost": 10,  # Moins cher
            "duration": 3500,
            "toll_count": 3
        }
        
        updated = manager.update_with_route(new_route, base_cost=20)
        
        assert updated is True
        assert manager.best_cheap["route"] == "new"
        assert manager.best_cheap["cost"] == 10
    
    def test_update_with_route_fastest(self):
        """Test mise à jour avec route plus rapide."""
        manager = RouteResultManager()
        manager.best_fast = {"route": "old", "cost": 10, "duration": 4000, "toll_count": 2}
        
        new_route = {
            "route": "new",
            "cost": 12,
            "duration": 3000,  # Plus rapide
            "toll_count": 2
        }
        
        updated = manager.update_with_route(new_route, base_cost=20)
        
        assert updated is True
        assert manager.best_fast["route"] == "new"
        assert manager.best_fast["duration"] == 3000
    
    def test_update_with_route_min_tolls(self):
        """Test mise à jour avec route moins de péages."""
        manager = RouteResultManager()
        manager.best_min_tolls = {"route": "old", "cost": 10, "duration": 3000, "toll_count": 3}
        
        new_route = {
            "route": "new",
            "cost": 15,
            "duration": 3500,
            "toll_count": 1  # Moins de péages
        }
        
        updated = manager.update_with_route(new_route, base_cost=20)
        
        assert updated is True
        assert manager.best_min_tolls["route"] == "new"
        assert manager.best_min_tolls["toll_count"] == 1
    
    def test_update_with_route_no_improvement(self):
        """Test mise à jour sans amélioration."""
        manager = RouteResultManager()
        manager.best_cheap = {"route": "old", "cost": 10, "duration": 3000, "toll_count": 2}
        manager.best_fast = {"route": "old", "cost": 10, "duration": 3000, "toll_count": 2}
        manager.best_min_tolls = {"route": "old", "cost": 10, "duration": 3000, "toll_count": 2}

        new_route = {
            "route": "new",
            "cost": 15,  # Plus cher
            "duration": 3500,  # Plus lent
            "toll_count": 3  # Plus de péages
        }

        updated = manager.update_with_route(new_route, base_cost=10)
        
        assert updated is False
        assert manager.best_cheap["route"] == "old"  # Pas changé
    
    def test_apply_fallback_if_needed_valid(self):
        """Test application fallback avec route valide."""
        manager = RouteResultManager()
        # Aucun résultat actuel
        base_route = {"features": [{"mock": "route"}]}
        
        manager.apply_fallback_if_needed(
            base_route=base_route,
            base_cost=12.5,
            base_duration=3600,
            base_toll_count=2,
            max_tolls=3
        )
        
        # Route de base devrait être appliquée comme fallback
        assert manager.best_fast["route"] == base_route
        assert manager.best_cheap["route"] == base_route
        assert manager.best_min_tolls["route"] == base_route
    
    def test_apply_fallback_if_needed_invalid(self):
        """Test application fallback avec route invalide."""
        manager = RouteResultManager()
        base_route = {"features": [{"mock": "route"}]}
        
        manager.apply_fallback_if_needed(
            base_route=base_route,
            base_cost=12.5,
            base_duration=3600,
            base_toll_count=4,  # Trop de péages
            max_tolls=3
        )
        
        # Route de base ne devrait pas être appliquée
        assert manager.best_fast["route"] is None
        assert manager.best_cheap["route"] is None
        assert manager.best_min_tolls["route"] is None
    
    def test_get_results(self):
        """Test récupération des résultats."""
        manager = RouteResultManager()
        manager.best_fast = {"route": "fast", "cost": 15}
        manager.best_cheap = {"route": "cheap", "cost": 10}
        manager.best_min_tolls = {"route": "min", "cost": 12}
        
        results = manager.get_results()
        
        assert results["fastest"]["route"] == "fast"
        assert results["cheapest"]["route"] == "cheap"
        assert results["min_tolls"]["route"] == "min"
    
    def test_has_valid_results_true(self):
        """Test vérification résultats valides."""
        manager = RouteResultManager()
        manager.best_fast = {"route": "some_route", "cost": 10}
        
        assert manager.has_valid_results() is True
    
    def test_has_valid_results_false(self):
        """Test vérification aucun résultat valide."""
        manager = RouteResultManager()
        
        assert manager.has_valid_results() is False
    
    def test_create_uniform_result(self):
        """Test création résultat uniforme."""
        route_result = {"route": "uniform", "cost": 10, "duration": 3000, "toll_count": 1}
        
        result = RouteResultManager.create_uniform_result(
            route_result, Config.StatusCodes.NO_TOLL_SUCCESS
        )
        
        assert result["fastest"] == route_result
        assert result["cheapest"] == route_result
        assert result["min_tolls"] == route_result
        assert result["status"] == Config.StatusCodes.NO_TOLL_SUCCESS