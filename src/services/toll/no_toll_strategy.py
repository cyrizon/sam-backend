"""
no_toll_strategy.py
------------------

Stratégie pour calculer des itinéraires sans péage.
Responsabilité unique : éviter complètement les péages.
"""

from benchmark.performance_tracker import performance_tracker
from src.services.toll.route_calculator import RouteCalculator
from src.services.toll.constants import TollOptimizationConfig as Config
from src.services.toll.exceptions import NoTollRouteError
from src.services.toll.error_handler import TollErrorHandler
from src.services.common.result_formatter import ResultFormatter
from src.services.common.toll_messages import TollMessages
from src.services.common.common_messages import CommonMessages
from src.services.ors_config_manager import ORSConfigManager


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
        self.route_calculator = RouteCalculator(ors_service)
    
    def compute_route_no_toll(self, coordinates, veh_class=Config.DEFAULT_VEH_CLASS):
        """
        Calcule un itinéraire sans péage en utilisant l'option avoid_features.
        """
        # Validation précoce des coordonnées
        try:
            ORSConfigManager.validate_coordinates(coordinates)
        except ValueError as e:
            return TollErrorHandler.handle_ors_error(e, "validation_coordinates")
        
        with performance_tracker.measure_operation(Config.Operations.COMPUTE_ROUTE_NO_TOLL):
            print(TollMessages.SEARCH_NO_TOLL)
            
            try:
                toll_free_route = self.route_calculator.get_route_avoid_tollways_with_tracking(coordinates)
                
                # Vérification avec le calculateur
                tolls_dict = self.route_calculator.locate_and_cost_tolls(
                    toll_free_route, veh_class, Config.Operations.LOCATE_TOLLS_NO_TOLL
                )
                tolls_on_route = tolls_dict["on_route"]
                
                if tolls_on_route:
                    print(CommonMessages.TOLLS_ON_ROUTE)
                    for toll in tolls_on_route:
                        print(f"  - {toll}")
                    cost = sum(t.get("cost", 0) for t in tolls_on_route)
                    
                    return ResultFormatter.format_route_result(
                        toll_free_route,
                        cost,
                        toll_free_route["features"][0]["properties"]["summary"]["duration"],
                        len(tolls_on_route)
                    ), Config.StatusCodes.SOME_TOLLS_PRESENT
                else:
                    print(CommonMessages.ROUTE_GRATUITE_TROUVEE)
                    return ResultFormatter.format_route_result(
                        toll_free_route,
                        0,
                        toll_free_route["features"][0]["properties"]["summary"]["duration"],
                        0
                    ), Config.StatusCodes.NO_TOLL_SUCCESS

            except Exception as e:
                return TollErrorHandler.handle_no_toll_route_error(e)
    
    def handle_no_toll_route(self, coordinates, veh_class=Config.DEFAULT_VEH_CLASS):
        """
        Gère le cas où aucun péage n'est autorisé.
        Point d'entrée principal pour les routes sans péage.
        
        Returns:
            dict: Résultat formaté avec fastest, cheapest, min_tolls, status        """
        from src.services.toll.result_manager import RouteResultManager
        
        with performance_tracker.measure_operation(Config.Operations.HANDLE_NO_TOLL_ROUTE):
            no_toll_result, status = self.compute_route_no_toll(coordinates, veh_class)
            
            if no_toll_result:
                return RouteResultManager.create_uniform_result(no_toll_result, status)
            else:
                # Import ici pour éviter les imports circulaires
                from src.services.toll.fallback_strategy import TollFallbackStrategy
                fallback = TollFallbackStrategy(self.ors)
                return fallback.handle_toll_failure(coordinates, max_tolls=0, veh_class=veh_class)