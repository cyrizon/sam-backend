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
                
                # Fallback automatique si échec ou si statut indique que le fallback est nécessaire
                if not result or self._should_trigger_fallback(result):
                    # Essayer d'extraire les données de route de base du résultat de la stratégie
                    base_data = self._extract_base_route_data_from_result(result)
                    result = self._handle_strategy_failure_with_base_data(
                        coordinates, max_price, max_price_percent, veh_class, max_comb_size, base_data
                    )
                
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
            return self.fallback_strategy.handle_budget_failure(
                coordinates, None, "none", veh_class=veh_class
            )
    def _should_trigger_fallback(self, result):
        """Détermine si le fallback doit être déclenché selon le statut du résultat."""
        if not result:
            return True
        
        # Statuts qui indiquent un échec nécessitant un fallback
        failure_statuses = {
            Config.StatusCodes.NO_ROUTE_WITHIN_BUDGET,
            Config.StatusCodes.NO_TOLLS_FOUND,
            Config.StatusCodes.NO_ALTERNATIVE_FOUND
        }
        
        return result.get("status") in failure_statuses
    
    def _extract_base_route_data_from_result(self, result):
        """Extrait les données de route de base d'un résultat de stratégie."""
        if not result:
            return None
        
        # Essayer d'extraire la route de base du fastest, cheapest ou min_tolls
        for key in ["fastest", "cheapest", "min_tolls"]:
            route_data = result.get(key)
            if route_data and route_data.get("route"):
                return {
                    "base_route": route_data["route"],
                    "base_cost": route_data.get("cost"),
                    "base_duration": route_data.get("duration"),
                    "base_toll_count": route_data.get("toll_count")
                }
        
        return None
    
    def _handle_strategy_failure_with_base_data(self, coordinates, max_price, max_price_percent, veh_class, max_comb_size, base_data):
        """Gère l'échec des stratégies avec données de base optionnelles."""
        budget_type = self._determine_budget_type(max_price, max_price_percent)
        budget_limit = max_price or max_price_percent
        
        # Utiliser les données de base si disponibles, sinon calculer
        if base_data:
            print(f"📋 Utilisation des données de route de base extraites du résultat de stratégie")
            return self.fallback_strategy.handle_budget_failure(
                coordinates, budget_limit, budget_type,
                base_route=base_data.get("base_route"),
                base_cost=base_data.get("base_cost"),
                base_duration=base_data.get("base_duration"),
                base_toll_count=base_data.get("base_toll_count"),
                veh_class=veh_class
            )
        else:
            # Fallback vers l'ancienne méthode si pas de données de base
            return self._handle_strategy_failure(coordinates, max_price, max_price_percent, veh_class, max_comb_size)

    def _handle_strategy_failure(self, coordinates, max_price, max_price_percent, veh_class, max_comb_size):
        """Gère l'échec des stratégies principales avec fallback."""
        budget_type = self._determine_budget_type(max_price, max_price_percent)
        budget_limit = max_price or max_price_percent
        
        # Calcul de la route de base pour éviter de la recalculer dans le fallback
        try:
            base_route = None
            base_cost = None
            base_duration = None
            base_toll_count = None
              # Essayer de calculer la route de base une seule fois
            base_route = self.absolute_budget_strategy.route_calculator.get_base_route_with_tracking(coordinates)
            if base_route:
                # Calculer les métriques de base
                tolls_dict = self.absolute_budget_strategy.route_calculator.locate_and_cost_tolls(base_route, veh_class)
                tolls_on_route = tolls_dict["on_route"]
                
                base_cost = sum(t.get("cost", 0) for t in tolls_on_route)
                base_duration = base_route["features"][0]["properties"]["summary"]["duration"]
                base_toll_count = len(tolls_on_route)
                
                print(f"📋 Route de base calculée pour fallback: {base_cost}€, {base_toll_count} péage(s)")
        except Exception as e:
            print(f"⚠️  Impossible de calculer la route de base pour le fallback: {e}")
        
        return self.fallback_strategy.handle_budget_failure(
            coordinates, budget_limit, budget_type, 
            base_route=base_route, base_cost=base_cost, 
            base_duration=base_duration, base_toll_count=base_toll_count,
            veh_class=veh_class
        )

    def _handle_critical_failure(self, coordinates, max_price, max_price_percent, veh_class, max_comb_size, error_message):
        """Gère les erreurs critiques avec fallback ultime."""
        try:
            budget_type = self._determine_budget_type(max_price, max_price_percent)
            budget_limit = max_price or max_price_percent
            
            # Essayer de calculer la route de base pour le fallback même en cas d'erreur critique
            base_route = None
            base_cost = None
            base_duration = None
            base_toll_count = None
            
            try:
                base_route = self.absolute_budget_strategy.route_calculator.get_base_route_with_tracking(coordinates)
                if base_route:
                    tolls_dict = self.absolute_budget_strategy.route_calculator.locate_and_cost_tolls(base_route, veh_class)
                    tolls_on_route = tolls_dict["on_route"]
                    
                    base_cost = sum(t.get("cost", 0) for t in tolls_on_route)
                    base_duration = base_route["features"][0]["properties"]["summary"]["duration"]
                    base_toll_count = len(tolls_on_route)
                    
                    print(f"📋 Route de base calculée pour fallback critique: {base_cost}€, {base_toll_count} péage(s)")
            except Exception as base_error:
                print(f"⚠️  Impossible de calculer la route de base pour le fallback critique: {base_error}")
            
            return self.fallback_strategy.handle_budget_failure(
                coordinates, budget_limit, "error", 
                base_route=base_route, base_cost=base_cost,
                base_duration=base_duration, base_toll_count=base_toll_count,
                veh_class=veh_class
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
