"""
fallback_strategy.py
-------------------

Stratégie de repli pour générer une route de base quand aucune solution n'est trouvée.
"""

from src.services.toll_locator import locate_tolls
from src.services.toll_cost import add_marginal_cost
from src.utils.route_utils import format_route_result
from benchmark.performance_tracker import performance_tracker


class FallbackStrategy:
    """
    Stratégie de repli pour les cas où aucune solution optimisée n'est trouvée.
    """
    
    def __init__(self, ors_service):
        self.ors = ors_service
    
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
        from src.services.toll.result_manager import RouteResultManager
        
        with performance_tracker.measure_operation("get_fallback_route"):
            with performance_tracker.measure_operation("ORS_base_route_fallback"):
                performance_tracker.count_api_call("ORS_base_route")
                base_route = self.ors.get_base_route(coordinates)
            
            with performance_tracker.measure_operation("locate_tolls_fallback"):
                tolls_on_route = locate_tolls(base_route, "data/barriers.csv")["on_route"]
                add_marginal_cost(tolls_on_route, veh_class)
            
            base_cost = sum(t.get("cost", 0) for t in tolls_on_route)
            base_duration = base_route["features"][0]["properties"]["summary"]["duration"]
            
            result = format_route_result(
                base_route,
                base_cost,
                base_duration,
                len(tolls_on_route)
            )
            
            return RouteResultManager.create_uniform_result(result, status)