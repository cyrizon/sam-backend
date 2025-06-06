"""
budget_strategies.py
------------------

Orchestrateur pour l'optimisation budgétaire - délégation pure comme toll_strategies.py
Responsabilité unique : déléguer aux stratégies spécialisées sans logique métier.
"""

from benchmark.performance_tracker import performance_tracker
from src.services.budget.zero_budget_strategy import ZeroBudgetStrategy
from src.services.budget.percentage_budget_strategy import PercentageBudgetStrategy
from src.services.budget.absolute_budget_strategy import AbsoluteBudgetStrategy
from src.services.budget.fallback_strategy import BudgetFallbackStrategy
from src.services.budget.constants import BudgetOptimizationConfig as Config
from src.services.budget.error_handler import BudgetErrorHandler


class BudgetRouteOptimizer:
    """
    Orchestrateur d'itinéraires avec contraintes budgétaires.
    Délégation pure aux stratégies spécialisées - aucune logique métier.
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
        Calcule un itinéraire avec contrainte budgétaire - délégation pure.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            max_price: Prix maximum en euros (absolu)
            max_price_percent: Pourcentage du coût de base (0.8 = 80%)
            veh_class: Classe de véhicule pour le calcul des coûts
            max_comb_size: Limite pour les combinaisons de péages à éviter
            
        Returns:
            dict: Résultats optimisés (fastest, cheapest, min_tolls, status)
        """
        
        BudgetErrorHandler.log_operation_start(
            "compute_route_with_budget_limit",
            max_price=max_price,
            max_price_percent=max_price_percent,
            veh_class=veh_class
        )
        
        with performance_tracker.measure_operation(Config.Operations.COMPUTE_ROUTE_WITH_BUDGET_LIMIT):
            try:
                # Validation précoce
                validation_error = BudgetErrorHandler.handle_budget_validation_error(max_price, max_price_percent)
                if validation_error:
                    BudgetErrorHandler.log_operation_failure("compute_route_with_budget_limit", "Validation failed")
                    return validation_error
                
                # Délégation pure - aucune logique métier
                result = self._delegate_to_strategy(coordinates, max_price, max_price_percent, veh_class, max_comb_size)
                
                # Fallback automatique si échec
                if not result:
                    result = self._handle_strategy_failure(coordinates, max_price, max_price_percent, veh_class, max_comb_size)
                
                BudgetErrorHandler.log_operation_success("compute_route_with_budget_limit", f"Status: {result.get('status', 'SUCCESS')}")
                return result
                
            except Exception as e:
                BudgetErrorHandler.log_operation_failure("compute_route_with_budget_limit", str(e))
                return self._handle_critical_failure(coordinates, max_price, max_price_percent, veh_class, max_comb_size, str(e))
    
    def _delegate_to_strategy(self, coordinates, max_price, max_price_percent, veh_class, max_comb_size):
        """Délègue à la stratégie appropriée selon les contraintes."""
        
        # Budget zéro
        if max_price == 0 or max_price_percent == 0:
            return self.zero_budget_strategy.handle_zero_budget_route(coordinates, veh_class)
        
        # Budget en pourcentage
        elif max_price_percent is not None:
            return self.percentage_budget_strategy.handle_percentage_budget_route(
                coordinates, max_price_percent, veh_class, max_comb_size
            )
        
        # Budget absolu
        elif max_price is not None:
            return self.absolute_budget_strategy.handle_absolute_budget_route(
                coordinates, max_price, veh_class, max_comb_size
            )
        
        # Aucune contrainte - meilleure solution globale
        else:
            return self.fallback_strategy.find_fastest_among_cheapest(coordinates, veh_class, max_comb_size)
    
    def _handle_strategy_failure(self, coordinates, max_price, max_price_percent, veh_class, max_comb_size):
        """Gère l'échec des stratégies principales avec fallback."""
        budget_type = self._determine_budget_type(max_price, max_price_percent)
        budget_limit = max_price or max_price_percent
        
        return self.fallback_strategy.handle_budget_failure(
            coordinates, budget_limit, budget_type, veh_class, max_comb_size
        )
    
    def _handle_critical_failure(self, coordinates, max_price, max_price_percent, veh_class, max_comb_size, error_message):
        """Gère les erreurs critiques avec fallback ultime."""
        try:
            budget_type = self._determine_budget_type(max_price, max_price_percent)
            budget_limit = max_price or max_price_percent
            
            return self.fallback_strategy.handle_budget_failure(
                coordinates, budget_limit, "error", veh_class, max_comb_size
            )
        except Exception:
            # Fallback ultime - route de base avec statut d'erreur critique
            return {
                "fastest": None,
                "cheapest": None,
                "min_tolls": None,
                "status": Config.StatusCodes.CRITICAL_ERROR,
                "error": error_message
            }
    
    def _determine_budget_type(self, max_price, max_price_percent):
        """Détermine le type de contrainte budgétaire."""
        if max_price == 0 or max_price_percent == 0:
            return "zero"
        elif max_price_percent is not None:
            return "percentage"
        elif max_price is not None:
            return "absolute"
        else:
            return "none"
