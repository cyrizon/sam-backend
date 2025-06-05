"""
fallback_strategy.py
-------------------

Stratégie de repli pour générer une route de base quand aucune solution n'est trouvée.
"""

from src.services.toll.error_handler import ErrorHandler
from src.services.common.result_formatter import ResultFormatter
from benchmark.performance_tracker import performance_tracker
from src.services.toll.route_calculator import RouteCalculator
from src.services.toll.constants import TollOptimizationConfig as Config
from src.services.ors_config_manager import ORSConfigManager


class FallbackStrategy:
    """
    Stratégie de repli pour les cas où aucune solution optimisée n'est trouvée.
    """
    
    def __init__(self, ors_service):
        self.ors = ors_service
        self.route_calculator = RouteCalculator(ors_service)  # Ajouter cette ligne
    
    def get_fallback_route(self, coordinates, veh_class, status):
        """
        Génère une route de base comme solution de repli.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            veh_class: Classe de véhicule pour le calcul des coûts
            status: Statut d'erreur à retourner
            
        Returns:
            dict: Route de base formatée avec format uniforme
        """
        # Validation précoce des coordonnées
        try:
            ORSConfigManager.validate_coordinates(coordinates)
        except ValueError as e:
            return ErrorHandler.handle_ors_error(e, "validation_coordinates")
        
        from src.services.toll.result_manager import RouteResultManager
        
        with performance_tracker.measure_operation(Config.Operations.GET_FALLBACK_ROUTE):
            base_route = self.route_calculator.get_base_route_with_tracking(coordinates)
            
            tolls_dict = self.route_calculator.locate_and_cost_tolls(
                base_route, veh_class, Config.Operations.LOCATE_TOLLS_FALLBACK
            )
            
            base_cost = sum(t.get("cost", 0) for t in tolls_dict["on_route"])
            base_duration = base_route["features"][0]["properties"]["summary"]["duration"]
            
            result = ResultFormatter.format_route_result(
                base_route,
                base_cost,
                base_duration,
                len(tolls_dict["on_route"])
            )
            
            return ResultFormatter.format_uniform_result(result, status)