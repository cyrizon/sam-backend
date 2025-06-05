"""
Tests pour ResultFormatter - Formatage centralisé des résultats.
"""
import pytest
from src.services.toll.result_formatter import ResultFormatter
from src.services.toll.constants import TollOptimizationConfig as Config


class TestResultFormatter:
    """Tests pour le formatage des résultats."""
    
    def test_format_route_result_basic(self):
        """Test formatage basique d'un résultat de route."""
        route = {"features": [{"geometry": {"coordinates": [[7, 48], [8, 49]]}}]}
        
        result = ResultFormatter.format_route_result(
            route=route,
            cost=12.345,
            duration=3600,
            toll_count=2
        )
        
        assert result["route"] == route
        assert result["cost"] == 12.35  # Arrondi à 2 décimales
        assert result["duration"] == 3600
        assert result["toll_count"] == 2
        assert "toll_id" not in result
    
    def test_format_route_result_with_toll_id(self):
        """Test formatage avec ID de péage."""
        route = {"mock": "route"}
        
        result = ResultFormatter.format_route_result(
            route=route,
            cost=0,
            duration=2400,
            toll_count=1,
            toll_id="toll_123"
        )
        
        assert result["toll_id"] == "toll_123"
        assert result["cost"] == 0
    
    def test_format_route_result_none_cost(self):
        """Test formatage avec coût None."""
        route = {"mock": "route"}
        
        result = ResultFormatter.format_route_result(
            route=route,
            cost=None,
            duration=1800,
            toll_count=0
        )
        
        assert result["cost"] == 0
    
    def test_format_optimization_results(self):
        """Test formatage des résultats d'optimisation."""
        fastest = {"cost": 10, "duration": 1800, "toll_count": 2}
        cheapest = {"cost": 5, "duration": 2400, "toll_count": 3}
        min_tolls = {"cost": 8, "duration": 2000, "toll_count": 1}
        
        result = ResultFormatter.format_optimization_results(
            fastest=fastest,
            cheapest=cheapest,
            min_tolls=min_tolls,
            status=Config.StatusCodes.MULTI_TOLL_SUCCESS
        )
        
        assert result["fastest"] == fastest
        assert result["cheapest"] == cheapest
        assert result["min_tolls"] == min_tolls
        assert result["status"] == Config.StatusCodes.MULTI_TOLL_SUCCESS
    
    def test_format_uniform_result(self):
        """Test formatage d'un résultat uniforme."""
        single_route = {"cost": 15, "duration": 3000, "toll_count": 2}
        
        result = ResultFormatter.format_uniform_result(
            single_route=single_route,
            status=Config.StatusCodes.NO_TOLL_SUCCESS
        )
        
        assert result["fastest"] == single_route
        assert result["cheapest"] == single_route
        assert result["min_tolls"] == single_route
        assert result["status"] == Config.StatusCodes.NO_TOLL_SUCCESS
    
    def test_format_summary_metrics_valid_route(self):
        """Test extraction de métriques d'une route valide."""
        route_result = {
            "route": {"mock": "data"},
            "cost": 12.50,
            "duration": 3600,
            "toll_count": 2,
            "toll_id": "toll_123"
        }
        
        metrics = ResultFormatter.format_summary_metrics(route_result)
        
        assert metrics["cost"] == 12.50
        assert metrics["duration_minutes"] == 60.0  # 3600/60
        assert metrics["toll_count"] == 2
        assert metrics["toll_id"] == "toll_123"
    
    def test_format_summary_metrics_empty_route(self):
        """Test extraction de métriques d'une route vide."""
        metrics = ResultFormatter.format_summary_metrics(None)
        
        assert metrics["cost"] is None
        assert metrics["duration_minutes"] is None
        assert metrics["toll_count"] is None
        assert metrics["toll_id"] is None
    
    def test_format_comparison_summary(self):
        """Test création d'un résumé comparatif."""
        optimization_results = {
            "fastest": {"route": {"mock": "data"}, "cost": 10, "duration": 1800, "toll_count": 2},
            "cheapest": {"route": {"mock": "data"}, "cost": 5, "duration": 2400, "toll_count": 3},
            "min_tolls": {"route": {"mock": "data"}, "cost": 8, "duration": 2000, "toll_count": 1},
            "status": Config.StatusCodes.MULTI_TOLL_SUCCESS
        }
        
        summary = ResultFormatter.format_comparison_summary(optimization_results)
        
        assert summary["fastest"]["cost"] == 10
        assert summary["fastest"]["duration_minutes"] == 30.0  # 1800/60
        assert summary["cheapest"]["cost"] == 5
        assert summary["min_tolls"]["toll_count"] == 1
        assert summary["status"] == Config.StatusCodes.MULTI_TOLL_SUCCESS
        assert summary["has_valid_routes"] is True
    
    def test_format_comparison_summary_no_valid_routes(self):
        """Test résumé comparatif sans routes valides."""
        optimization_results = {
            "fastest": None,
            "cheapest": None,
            "min_tolls": None,
            "status": "NO_SOLUTION"
        }
        
        summary = ResultFormatter.format_comparison_summary(optimization_results)
        
        assert summary["has_valid_routes"] is False