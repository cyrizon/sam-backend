"""
budget_strategies.py
------------------

Orchestrateur pour l'optimisation budgétaire - refactorisé pour une meilleure séparation des responsabilités.
Responsabilité unique : déléguer aux stratégies spécialisées et coordonner le flux principal.
"""

from benchmark.performance_tracker import performance_tracker
from src.services.budget.zero_budget_strategy import ZeroBudgetStrategy
from src.services.budget.percentage_budget_strategy import PercentageBudgetStrategy
from src.services.budget.absolute_budget_strategy import AbsoluteBudgetStrategy
from src.services.budget.fallback_strategy import BudgetFallbackStrategy
from src.services.budget.constants import BudgetOptimizationConfig as Config
from src.services.budget.error_handler import BudgetErrorHandler
from src.services.budget.feasibility_checker import BudgetFeasibilityChecker
from src.services.budget.failure_handler import BudgetFailureHandler


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
        
        # Stratégies spécialisées
        self.zero_budget_strategy = ZeroBudgetStrategy(ors_service)
        self.percentage_budget_strategy = PercentageBudgetStrategy(ors_service)
        self.absolute_budget_strategy = AbsoluteBudgetStrategy(ors_service)
        self.fallback_strategy = BudgetFallbackStrategy(ors_service)
        
        # Composants d'aide
        self.feasibility_checker = BudgetFeasibilityChecker(ors_service)
        self.failure_handler = BudgetFailureHandler(ors_service, self.fallback_strategy)
    
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
                
                # Vérification précoce de faisabilité budgétaire AVANT les calculs coûteux
                if self.feasibility_checker.should_check_feasibility(max_price, max_price_percent):
                    early_fallback_needed = self.feasibility_checker.check_budget_feasibility_early(
                        coordinates, max_price, max_price_percent, veh_class
                    )
                    if early_fallback_needed:
                        print("🚫 Budget manifestement trop bas - Fallback immédiat (économie de calculs)")
                        return self.failure_handler.handle_strategy_failure_with_base_data(
                            coordinates, max_price, max_price_percent, veh_class, max_comb_size, None
                        )
                
                # Délégation pure - aucune logique métier (seulement si budget potentiellement faisable)
                result = self._delegate_to_strategy(coordinates, max_price, max_price_percent, veh_class, max_comb_size)
                
                # Fallback automatique si échec ou si statut indique que le fallback est nécessaire
                if not result or self.failure_handler.should_trigger_fallback(result):
                    # Essayer d'extraire les données de route de base du résultat de la stratégie
                    base_data = self.failure_handler.extract_base_route_data_from_result(result)
                    result = self.failure_handler.handle_strategy_failure_with_base_data(
                        coordinates, max_price, max_price_percent, veh_class, max_comb_size, base_data
                    )
                
                BudgetErrorHandler.log_operation_success("compute_route_with_budget_limit", f"Status: {result.get('status', 'SUCCESS')}")
                return result
                
            except Exception as e:
                BudgetErrorHandler.log_operation_failure("compute_route_with_budget_limit", str(e))
                return self.failure_handler.handle_critical_failure(
                    coordinates, max_price, max_price_percent, veh_class, max_comb_size, str(e)
                )
    
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
            return self.fallback_strategy.handle_budget_failure(
                coordinates, None, "none", veh_class=veh_class
            )