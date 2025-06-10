"""
failure_handler.py
-----------------

Gestionnaire des échecs et fallbacks pour l'optimisation budgétaire.
Responsabilité unique : gérer tous les types d'échecs et coordonner les fallbacks.
"""

from src.services.budget.constants import BudgetOptimizationConfig as Config


class BudgetFailureHandler:
    """Gestionnaire centralisé des échecs et stratégies de fallback."""
    
    def __init__(self, ors_service, fallback_strategy):
        self.ors = ors_service
        self.fallback_strategy = fallback_strategy
    
    def should_trigger_fallback(self, result):
        """Détermine si le fallback doit être déclenché selon le statut du résultat."""
        if not result:
            return True
        # Statuts qui indiquent un échec nécessitant un fallback
        failure_statuses = {
            Config.StatusCodes.NO_ROUTE_WITHIN_BUDGET,
            Config.StatusCodes.NO_TOLLS_FOUND,
            Config.StatusCodes.NO_ALTERNATIVE_FOUND,
            Config.StatusCodes.PERCENTAGE_BUDGET_IMPOSSIBLE,  # Nouveau statut
            Config.StatusCodes.NO_ROUTE_WITHIN_BUDGET_RETURNING_FASTEST_AMONG_CHEAPEST
        }
        
        return result.get("status") in failure_statuses
    
    def extract_base_route_data_from_result(self, result):
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
    
    def handle_strategy_failure_with_base_data(self, coordinates, max_price, max_price_percent, veh_class, max_comb_size, base_data):
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
            from src.services.budget.absolute_budget_strategy import AbsoluteBudgetStrategy
            absolute_strategy = AbsoluteBudgetStrategy(self.ors)
            base_route = absolute_strategy.route_calculator.get_base_route_with_tracking(coordinates)
            
            if base_route:
                # Calculer les métriques de base
                tolls_dict = absolute_strategy.route_calculator.locate_and_cost_tolls(base_route, veh_class)
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

    def handle_critical_failure(self, coordinates, max_price, max_price_percent, veh_class, max_comb_size, error_message):
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
                from src.services.budget.absolute_budget_strategy import AbsoluteBudgetStrategy
                absolute_strategy = AbsoluteBudgetStrategy(self.ors)
                base_route = absolute_strategy.route_calculator.get_base_route_with_tracking(coordinates)
                
                if base_route:
                    tolls_dict = absolute_strategy.route_calculator.locate_and_cost_tolls(base_route, veh_class)
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
