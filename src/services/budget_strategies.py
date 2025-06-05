"""
budget_strategies.py
------------------

Stratégies pour calculer des itinéraires avec des contraintes budgétaires.
Intègre le système de mesure des performances pour optimiser les appels.
"""

from benchmark.performance_tracker import performance_tracker
from src.services.budget.zero_budget_strategy import ZeroBudgetStrategy
from src.services.budget.percentage_budget_strategy import PercentageBudgetStrategy
from src.services.budget.absolute_budget_strategy import AbsoluteBudgetStrategy
from src.services.budget.fallback_strategy import BudgetFallbackStrategy
from src.services.budget.constants import BudgetOptimizationConfig as Config
from src.services.budget.error_handler import BudgetErrorHandler
from src.services.toll.result_formatter import ResultFormatter
from itertools import combinations
from src.services.toll_locator import locate_tolls, get_all_open_tolls_by_proximity
from src.services.toll_cost import add_marginal_cost
from src.utils.poly_utils import avoidance_multipolygon

class BudgetRouteOptimizer:
    """
    Optimiseur d'itinéraires avec contraintes budgétaires.
    Intègre le tracking des performances pour analyser et optimiser les appels.
    """
    
    def __init__(self, ors_service):
        """
        Initialise l'optimiseur avec un service ORS.
        
        Args:
            ors_service: Instance de ORSService pour les appels API
        """
        self.ors = ors_service
        self.zero_budget_strategy = ZeroBudgetStrategy(ors_service)
        self.percentage_budget_strategy = PercentageBudgetStrategy(ors_service)
        self.absolute_budget_strategy = AbsoluteBudgetStrategy(ors_service)
        self.fallback_strategy = BudgetFallbackStrategy(ors_service)
    
    def compute_route_with_budget_limit(
        self,
        coordinates,
        max_price=None,
        max_price_percent=None,
        veh_class=Config.DEFAULT_VEH_CLASS,
        max_comb_size=Config.DEFAULT_MAX_COMB_SIZE
    ):
        """
        Calcule un itinéraire avec une contrainte de budget maximum.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            max_price: Prix maximum en euros (absolu)
            max_price_percent: Pourcentage du coût de base (0.8 = 80%)
            veh_class: Classe de véhicule pour le calcul des coûts
            max_comb_size: Limite pour les combinaisons de péages à éviter
            
        Returns:
            dict: Résultats optimisés (fastest, cheapest, min_tolls, status)
        """
        
        # Log du début de l'opération
        BudgetErrorHandler.log_operation_start(
            "compute_route_with_budget_limit",
            max_price=max_price,
            max_price_percent=max_price_percent,
            veh_class=veh_class,
            max_comb_size=max_comb_size
        )
        
        with performance_tracker.measure_operation(Config.Operations.COMPUTE_ROUTE_WITH_BUDGET_LIMIT, {
            "max_price": max_price,
            "max_price_percent": max_price_percent,
            "veh_class": veh_class,
            "max_comb_size": max_comb_size
        }):
            print(f"=== Calcul d'itinéraire avec contrainte de budget ===")
            
            try:
                # CORRECTION 2: Validation précoce des paramètres
                validation_error = BudgetErrorHandler.handle_budget_validation_error(max_price, max_price_percent)
                if validation_error:
                    return validation_error
                
                # CORRECTION 3: Délégation claire avec gestion des échecs
                result = None
                
                # Cas spécial 1: Budget zéro ou pourcentage zéro
                if max_price == 0 or max_price_percent == 0:
                    result = self._handle_zero_budget_route(coordinates, veh_class)
                
                # Cas spécial 2: Contrainte en pourcentage
                elif max_price_percent is not None:
                    result = self._handle_percentage_budget_route(coordinates, max_price_percent, veh_class, max_comb_size)
                
                # Cas spécial 3: Contrainte absolue en euros
                elif max_price is not None:
                    result = self._handle_absolute_budget_route(coordinates, max_price, veh_class, max_comb_size)
                
                # Cas par défaut: aucune contrainte
                else:
                    result = self._handle_no_budget_constraint(coordinates, veh_class, max_comb_size)
                
                # CORRECTION 4: Gestion du fallback si la stratégie échoue
                if not result or not self._is_valid_result(result):
                    print("La stratégie principale a échoué, activation du fallback...")
                    result = self._handle_fallback(coordinates, max_price, max_price_percent, veh_class, max_comb_size)
                
                # Log du succès
                if result and result.get("status"):
                    BudgetErrorHandler.log_operation_success(
                        "compute_route_with_budget_limit",
                        f"Status: {result['status']}"
                    )
                
                return result
                
            except Exception as e:
                BudgetErrorHandler.log_operation_failure("compute_route_with_budget_limit", str(e))
                # Fallback ultime en cas d'erreur
                return self._handle_critical_error(coordinates, veh_class, str(e))
    
    def _handle_zero_budget_route(self, coordinates, veh_class):
        """Délègue à la stratégie spécialisée pour budget zéro"""
        try:
            return self.zero_budget_strategy.handle_zero_budget_route(coordinates, veh_class)
        except Exception as e:
            print(f"Erreur dans ZeroBudgetStrategy: {e}")
            return self.fallback_strategy.handle_budget_failure(coordinates, 0, "zero", veh_class)
    
    def _handle_percentage_budget_route(self, coordinates, max_price_percent, veh_class, max_comb_size):
        """Délègue à la stratégie spécialisée pour budget en pourcentage"""
        try:
            return self.percentage_budget_strategy.handle_percentage_budget_route(coordinates, max_price_percent, veh_class, max_comb_size)
        except Exception as e:
            print(f"Erreur dans PercentageBudgetStrategy: {e}")
            return self.fallback_strategy.handle_budget_failure(coordinates, max_price_percent, "percentage", veh_class, max_comb_size)
    
    def _handle_absolute_budget_route(self, coordinates, max_price, veh_class, max_comb_size):
        """Délègue à la stratégie spécialisée pour budget absolu"""
        try:
            return self.absolute_budget_strategy.handle_absolute_budget_route(coordinates, max_price, veh_class, max_comb_size)
        except Exception as e:
            print(f"Erreur dans AbsoluteBudgetStrategy: {e}")
            return self.fallback_strategy.handle_budget_failure(coordinates, max_price, "absolute", veh_class, max_comb_size)
    
    def _handle_no_budget_constraint(self, coordinates, veh_class, max_comb_size):
        """Délègue à la stratégie de fallback pour trouver la meilleure solution"""
        try:
            return self.fallback_strategy.find_fastest_among_cheapest(coordinates, veh_class, max_comb_size)
        except Exception as e:
            print(f"Erreur dans la recherche fastest among cheapest: {e}")
            return self.fallback_strategy.handle_budget_failure(coordinates, None, "none", veh_class, max_comb_size)
    
    def _handle_fallback(self, coordinates, max_price, max_price_percent, veh_class, max_comb_size):
        """Gère le fallback quand les stratégies principales échouent."""
        try:
            if max_price == 0 or max_price_percent == 0:
                budget_type = "zero"
                budget_limit = 0
            elif max_price_percent is not None:
                budget_type = "percentage"
                budget_limit = max_price_percent
            elif max_price is not None:
                budget_type = "absolute"
                budget_limit = max_price
            else:
                budget_type = "none"
                budget_limit = None
            
            return self.fallback_strategy.handle_budget_failure(coordinates, budget_limit, budget_type, veh_class, max_comb_size)
        except Exception as e:
            print(f"Erreur dans le fallback: {e}")
            return self._handle_critical_error(coordinates, veh_class, str(e))
    
    def _handle_critical_error(self, coordinates, veh_class, error_message):
        """Gère les erreurs critiques avec fallback ultime."""
        try:
            # Tentative de route de base en dernier recours
            base_route = self.ors.get_base_route(coordinates)
            tolls_dict = locate_tolls(base_route, Config.get_barriers_csv_path())
            tolls_on_route = tolls_dict["on_route"]
            add_marginal_cost(tolls_on_route, veh_class)
            
            cost = sum(t.get("cost", 0) for t in tolls_on_route)
            duration = base_route["features"][0]["properties"]["summary"]["duration"]
            toll_count = len(tolls_on_route)
            
            base_result = ResultFormatter.format_route_result(base_route, cost, duration, toll_count)
            
            return ResultFormatter.format_optimization_results(
                fastest=base_result,
                cheapest=base_result,
                min_tolls=base_result,
                status=Config.StatusCodes.CRITICAL_ERROR
            )
        except Exception:
            # Erreur critique complète
            return ResultFormatter.format_optimization_results(
                fastest=None,
                cheapest=None,
                min_tolls=None,
                status=Config.StatusCodes.CRITICAL_ERROR
            )
    
    def _is_valid_result(self, result):
        """Vérifie si un résultat est valide."""
        if not result or not isinstance(result, dict):
            return False
        
        # Vérifier qu'au moins un des résultats principaux existe
        fastest = result.get("fastest")
        cheapest = result.get("cheapest")
        min_tolls = result.get("min_tolls")
        
        return any(r is not None and r.get("route") is not None for r in [fastest, cheapest, min_tolls])
