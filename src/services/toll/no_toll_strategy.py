"""
no_toll_strategy.py
------------------

Stratégie pour calculer des itinéraires sans péage.
Responsabilité unique : éviter complètement les péages.
"""

from src.utils.route_utils import format_route_result
from benchmark.performance_tracker import performance_tracker
from src.services.toll.route_calculator import RouteCalculator
from src.services.toll.constants import TollOptimizationConfig as Config
from src.services.toll.exceptions import NoTollRouteError
from src.services.toll.error_handler import ErrorHandler


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
    
    def compute_route_no_toll(self, coordinates, veh_class=Config.DEFAULT_VEH_CLASS):
        """
        Calcule un itinéraire sans péage en utilisant l'option avoid_features.
        """
        with performance_tracker.measure_operation(Config.Operations.COMPUTE_ROUTE_NO_TOLL):
            print(Config.Messages.SEARCH_NO_TOLL)
            
            try:
                toll_free_route = self.route_calculator.get_route_avoid_tollways_with_tracking(coordinates)
                
                # Vérification avec le calculateur
                tolls_dict = self.route_calculator.locate_and_cost_tolls(
                    toll_free_route, veh_class, Config.Operations.LOCATE_TOLLS_NO_TOLL
                )
                tolls_on_route = tolls_dict["on_route"]
                
                if tolls_on_route:
                    print(Config.Messages.ATTENTION_TOLLS_PRESENT.format(count=len(tolls_on_route)))
                    cost = sum(t.get("cost", 0) for t in tolls_on_route)
                    
                    return format_route_result(
                        toll_free_route,
                        cost,
                        toll_free_route["features"][0]["properties"]["summary"]["duration"],
                        len(tolls_on_route)
                    ), Config.StatusCodes.SOME_TOLLS_PRESENT
                else:
                    return format_route_result(
                        toll_free_route,
                        0,
                        toll_free_route["features"][0]["properties"]["summary"]["duration"],
                        0
                    ), Config.StatusCodes.NO_TOLL_SUCCESS

            except Exception as e:
                return ErrorHandler.handle_no_toll_route_error(e)
    
    def handle_no_toll_route(self, coordinates, veh_class=Config.DEFAULT_VEH_CLASS):
        """
        Gère le cas où aucun péage n'est autorisé.
        Point d'entrée principal pour les routes sans péage.
        
        Returns:
            dict: Résultat formaté avec fastest, cheapest, min_tolls, status
        """
        from src.services.toll.result_manager import RouteResultManager
        
        with performance_tracker.measure_operation(Config.Operations.HANDLE_NO_TOLL_ROUTE):
            no_toll_result, status = self.compute_route_no_toll(coordinates, veh_class)
            
            if no_toll_result:
                return RouteResultManager.create_uniform_result(no_toll_result, status)
            else:
                # Import ici pour éviter les imports circulaires
                from src.services.toll.fallback_strategy import FallbackStrategy
                fallback = FallbackStrategy(self.ors)
                return fallback.get_fallback_route(coordinates, veh_class, status)