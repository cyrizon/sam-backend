"""
no_toll_strategy.py
------------------

Stratégie pour calculer des itinéraires sans péage.
Responsabilité unique : éviter complètement les péages.
"""

from src.utils.route_utils import format_route_result
from benchmark.performance_tracker import performance_tracker
from src.services.toll.route_calculator import RouteCalculator


class NoTollStrategy:
    """
    Stratégie pour calculer des itinéraires sans péage.
    """
    
    def __init__(self, ors_service):
        """
        Initialise la stratégie avec un service ORS.
        
        Args:
            ors_service: Instance de ORSService pour les appels API
        """
        self.ors = ors_service
        self.route_calculator = RouteCalculator(ors_service)  # Ajouter cette ligne
    
    def compute_route_no_toll(self, coordinates, veh_class="c1"):
        """
        Calcule un itinéraire sans péage en utilisant l'option avoid_features.
        """
        with performance_tracker.measure_operation("compute_route_no_toll"):
            print("Recherche d'un itinéraire sans péage...")
            
            try:
                toll_free_route = self.route_calculator.get_route_avoid_tollways_with_tracking(coordinates)
                
                # Vérification avec le calculateur
                tolls_dict = self.route_calculator.locate_and_cost_tolls(
                    toll_free_route, veh_class, "locate_tolls_no_toll"
                )
                tolls_on_route = tolls_dict["on_route"]
                
                if tolls_on_route:
                    print(f"Attention: l'itinéraire sans péage contient quand même {len(tolls_on_route)} péages")
                    cost = sum(t.get("cost", 0) for t in tolls_on_route)
                    
                    return format_route_result(
                        toll_free_route,
                        cost,
                        toll_free_route["features"][0]["properties"]["summary"]["duration"],
                        len(tolls_on_route)
                    ), "SOME_TOLLS_PRESENT"
                else:
                    return format_route_result(
                        toll_free_route,
                        0,
                        toll_free_route["features"][0]["properties"]["summary"]["duration"],
                        0
                    ), "NO_TOLL_SUCCESS"
            
            except Exception as e:
                performance_tracker.log_error(f"Impossible de trouver un itinéraire sans péage: {e}")
                print(f"Impossible de trouver un itinéraire sans péage: {e}")
                return None, "NO_TOLL_ROUTE_NOT_POSSIBLE"
    
    def handle_no_toll_route(self, coordinates, veh_class="c1"):
        """
        Gère le cas où aucun péage n'est autorisé.
        Point d'entrée principal pour les routes sans péage.
        
        Returns:
            dict: Résultat formaté avec fastest, cheapest, min_tolls, status
        """
        from src.services.toll.result_manager import RouteResultManager
        
        with performance_tracker.measure_operation("handle_no_toll_route"):
            no_toll_result, status = self.compute_route_no_toll(coordinates, veh_class)
            
            if no_toll_result:
                return RouteResultManager.create_uniform_result(no_toll_result, status)
            else:
                # Import ici pour éviter les imports circulaires
                from src.services.toll.fallback_strategy import FallbackStrategy
                fallback = FallbackStrategy(self.ors)
                return fallback.get_fallback_route(coordinates, veh_class, status)