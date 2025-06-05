"""
zero_budget_strategy.py
----------------------

Stratégie pour calculer des itinéraires avec budget zéro (routes gratuites).
Responsabilité unique : trouver des routes sans frais de péage.
"""

from benchmark.performance_tracker import performance_tracker
from src.services.budget.constants import BudgetOptimizationConfig as Config
from src.services.common.result_formatter import ResultFormatter
from src.services.budget.result_manager import BudgetRouteResultManager as RouteResultManager
from src.services.toll.route_calculator import RouteCalculator
from src.services.toll.error_handler import ErrorHandler
from src.services.ors_config_manager import ORSConfigManager

class ZeroBudgetStrategy:
    """
    Stratégie pour calculer des itinéraires avec budget zéro.
    """
    
    def __init__(self, ors_service):
        """
        Initialise la stratégie avec un service ORS.
        
        Args:
            ors_service: Instance de ORSService pour les appels API
        """
        self.ors = ors_service
        self.route_calculator = RouteCalculator(ors_service)
    
    def compute_zero_budget_route(self, coordinates, veh_class=Config.DEFAULT_VEH_CLASS):
        """
        Calcule un itinéraire gratuit en évitant tous les péages.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            veh_class: Classe de véhicule
            
        Returns:
            dict: Résultat formaté ou erreur
        """
        # Validation précoce des coordonnées
        try:
            ORSConfigManager.validate_coordinates(coordinates)
        except ValueError as e:
            return ErrorHandler.handle_ors_error(e, "validation_coordinates")
        
        with performance_tracker.measure_operation(Config.Operations.HANDLE_ZERO_BUDGET_ROUTE):
            print(Config.Messages.SEARCH_ZERO_BUDGET)
            
            try:
                # Tenter d'obtenir une route sans péage
                toll_free_route = self.route_calculator.get_route_avoid_tollways_with_tracking(coordinates)
                
                # Vérifier les péages présents malgré l'évitement
                tolls_dict = self.route_calculator.locate_and_cost_tolls(
                    toll_free_route, veh_class, Config.Operations.LOCATE_TOLLS_ZERO_BUDGET
                )
                tolls_on_route = tolls_dict["on_route"]
                
                # Calculer les métriques
                cost = sum(t.get("cost", 0) for t in tolls_on_route)
                duration = toll_free_route["features"][0]["properties"]["summary"]["duration"]
                toll_count = len(tolls_on_route)
                
                # Créer le résultat formaté avec le formatter toll standard
                route_result = ResultFormatter.format_route_result(
                    toll_free_route, cost, duration, toll_count
                )
                
                # Vérifier si des péages sont présents malgré l'évitement
                tolls_present = toll_count > 0
                if tolls_present:
                    print(Config.Messages.ATTENTION_TOLLS_PRESENT.format(count=toll_count))
                    status = Config.StatusCodes.BUDGET_ZERO_SOME_TOLLS_PRESENT
                else:
                    status = Config.StatusCodes.BUDGET_ZERO_NO_TOLL_SUCCESS
                
                # Retourner le résultat uniforme (format toll standard)
                return ResultFormatter.format_uniform_result(route_result, status)
                
            except Exception as e:
                print(Config.Messages.IMPOSSIBLE_NO_TOLL_ROUTE.format(error=str(e)))
                return ErrorHandler.handle_ors_error(e, Config.Operations.HANDLE_ZERO_BUDGET_ROUTE)
    
    def handle_zero_budget_route(self, coordinates, veh_class=Config.DEFAULT_VEH_CLASS):
        """
        Point d'entrée principal pour les routes avec budget zéro.
        
        Returns:
            dict: Résultat formaté avec fastest, cheapest, min_tolls, status
        """
        with performance_tracker.measure_operation(Config.Operations.COMPUTE_ROUTE_ZERO_BUDGET):
            return self.compute_zero_budget_route(coordinates, veh_class)