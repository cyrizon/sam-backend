"""
result_manager.py
----------------

Gestionnaire pour comparer et sélectionner les meilleurs itinéraires budgétaires.
Responsabilité unique : gérer les critères d'optimisation avec contraintes budgétaires.
"""

from src.services.common.result_formatter import ResultFormatter
from src.services.budget.constants import BudgetOptimizationConfig as Config
from src.services.budget.route_validator import BudgetRouteValidator
from src.services.common.common_messages import CommonMessages
from src.services.common.budget_messages import BudgetMessages


class BudgetRouteResultManager:
    """Gestionnaire de résultats spécialisé pour les contraintes budgétaires."""
    
    def __init__(self, budget_limit=None, budget_type="none"):
        """
        Initialise le gestionnaire avec contrainte budgétaire.
        
        Args:
            budget_limit: Limite budgétaire (euros ou pourcentage)
            budget_type: Type de budget ("zero", "absolute", "percentage", "none")
        """
        # Résultats optimaux
        self.best_fast = {"route": None, "cost": float('inf'), "duration": float('inf'), "toll_count": float('inf')}
        self.best_cheap = {"route": None, "cost": float('inf'), "duration": float('inf'), "toll_count": float('inf')}
        self.best_min_tolls = {"route": None, "cost": float('inf'), "duration": float('inf'), "toll_count": float('inf')}
        
        # Contrainte budgétaire
        self.budget_limit = budget_limit
        self.budget_type = budget_type
        
        # Statistiques
        self.routes_tested = 0
        self.routes_within_budget = 0
    
    def initialize_with_base_route(self, base_route, base_cost, base_duration, base_toll_count):
        """
        Initialise les résultats avec la route de base si elle respecte le budget.
        
        Args:
            base_route: Route de base
            base_cost: Coût de la route de base
            base_duration: Durée de la route de base
            base_toll_count: Nombre de péages de la route de base
        """
        if self._is_within_budget(base_cost):
            base_result = ResultFormatter.format_route_result(base_route, base_cost, base_duration, base_toll_count)
            self.best_cheap = base_result.copy()
            self.best_fast = base_result.copy()
            self.best_min_tolls = base_result.copy()
            self.routes_within_budget += 1
    
    def update_with_route(self, route_data, base_cost):
        """
        Met à jour les meilleurs résultats avec un nouveau candidat d'itinéraire.
        
        Args:
            route_data: Données de l'itinéraire (doit contenir cost, duration, toll_count)
            base_cost: Coût de la route de base pour comparaison
            
        Returns:
            bool: True si au moins un résultat a été mis à jour
        """
        self.routes_tested += 1
        
        cost = route_data["cost"]
        duration = route_data["duration"]
        toll_count = route_data["toll_count"]
        
        # Vérifier si respecte le budget
        within_budget = self._is_within_budget(cost)
        if within_budget:
            self.routes_within_budget += 1
        
        updated = False
        
        # Mise à jour de l'itinéraire avec le moins de péages (priorité aux routes dans le budget)
        if self._is_better_min_tolls(route_data, within_budget):
            self.best_min_tolls = route_data.copy()
            updated = True
        
        # Mise à jour de l'itinéraire le moins cher (priorité aux routes dans le budget)
        if self._is_better_cheapest(route_data, within_budget):
            self.best_cheap = route_data.copy()
            updated = True
        
        # Mise à jour de l'itinéraire le plus rapide (priorité aux routes dans le budget)
        if self._is_better_fastest(route_data, within_budget):
            self.best_fast = route_data.copy()
            updated = True
        
        return updated
    
    def _is_within_budget(self, cost):
        """Vérifie si un coût respecte la contrainte budgétaire."""
        if self.budget_limit is None:
            return True
        
        if self.budget_type == "zero":
            return cost == 0
        elif self.budget_type in ["absolute", "percentage"]:
            return cost <= self.budget_limit
        else:
            return True
    
    def _is_better_min_tolls(self, route_data, within_budget):
        """Détermine si une route est meilleure pour le critère min_tolls."""
        current_within_budget = self._is_within_budget(self.best_min_tolls["cost"])
        
        # Priorité aux routes dans le budget
        if within_budget and not current_within_budget:
            return True
        if not within_budget and current_within_budget:
            return False
        
        # Même statut budget : comparer par nombre de péages, puis coût, puis durée
        if route_data["toll_count"] < self.best_min_tolls["toll_count"]:
            return True
        elif route_data["toll_count"] == self.best_min_tolls["toll_count"]:
            if route_data["cost"] < self.best_min_tolls["cost"]:
                return True
            elif route_data["cost"] == self.best_min_tolls["cost"]:
                return route_data["duration"] < self.best_min_tolls["duration"]
        
        return False
    
    def _is_better_cheapest(self, route_data, within_budget):
        """Détermine si une route est meilleure pour le critère cheapest."""
        current_within_budget = self._is_within_budget(self.best_cheap["cost"])
        
        # Priorité aux routes dans le budget
        if within_budget and not current_within_budget:
            return True
        if not within_budget and current_within_budget:
            return False
        
        # Même statut budget : comparer par coût, puis durée, puis péages
        if route_data["cost"] < self.best_cheap["cost"]:
            return True
        elif route_data["cost"] == self.best_cheap["cost"]:
            if route_data["duration"] < self.best_cheap["duration"]:
                return True
            elif route_data["duration"] == self.best_cheap["duration"]:
                return route_data["toll_count"] < self.best_cheap["toll_count"]
        
        return False
    
    def _is_better_fastest(self, route_data, within_budget):
        """Détermine si une route est meilleure pour le critère fastest."""
        current_within_budget = self._is_within_budget(self.best_fast["cost"])
        
        # Priorité aux routes dans le budget
        if within_budget and not current_within_budget:
            return True
        if not within_budget and current_within_budget:
            return False
        
        # Même statut budget : comparer par durée, puis coût, puis péages
        if route_data["duration"] < self.best_fast["duration"]:
            return True
        elif route_data["duration"] == self.best_fast["duration"]:
            if route_data["cost"] < self.best_fast["cost"]:
                return True
            elif route_data["cost"] == self.best_fast["cost"]:
                return route_data["toll_count"] < self.best_fast["toll_count"]
        
        return False
    
    def has_valid_results(self):
        """Vérifie si au moins un résultat valide existe."""
        return (self.best_fast["route"] is not None or 
                self.best_cheap["route"] is not None or 
                self.best_min_tolls["route"] is not None)
    
    def has_budget_compliant_results(self):
        """Vérifie si au moins un résultat respecte le budget."""
        return (self._is_within_budget(self.best_fast["cost"]) or
                self._is_within_budget(self.best_cheap["cost"]) or
                self._is_within_budget(self.best_min_tolls["cost"]))
    
    def get_results(self):
        """Retourne les résultats finaux."""
        return {
            "fastest": self.best_fast,
            "cheapest": self.best_cheap,
            "min_tolls": self.best_min_tolls
        }
    
    def get_budget_statistics(self):
        """Retourne les statistiques budgétaires."""
        return {
            "routes_tested": self.routes_tested,
            "routes_within_budget": self.routes_within_budget,
            "budget_compliance_rate": (self.routes_within_budget / max(1, self.routes_tested)) * 100,
            "has_budget_solutions": self.has_budget_compliant_results()
        }
    
    def apply_fallback_if_needed(self, base_route, base_cost, base_duration, base_toll_count):
        """
        Applique la route de base comme solution de repli si nécessaire.
        
        Args:
            base_route: Route de base
            base_cost: Coût de la route de base
            base_duration: Durée de la route de base
            base_toll_count: Nombre de péages de la route de base
        """
        base_result = ResultFormatter.format_route_result(base_route, base_cost, base_duration, base_toll_count)
        
        if self.best_fast["route"] is None:
            self.best_fast = base_result.copy()
            
        if self.best_cheap["route"] is None:
            self.best_cheap = base_result.copy()
            
        if self.best_min_tolls["route"] is None:
            self.best_min_tolls = base_result.copy()
    
    def log_budget_results(self, base_toll_count, base_cost, base_duration):
        """
        Affiche un résumé des résultats finaux avec focus budget.
        
        Args:
            base_toll_count: Nombre de péages de la route de base
            base_cost: Coût de la route de base
            base_duration: Durée de la route de base
        """
        print(BudgetMessages.BASE_ROUTE_SUMMARY.format(
            toll_count=base_toll_count, 
            cost=base_cost, 
            duration=base_duration/60
        ))
        
        # Statistiques budgétaires
        stats = self.get_budget_statistics()
        print(BudgetMessages.BUDGET_STATISTICS.format(
            routes_tested=stats['routes_tested'],
            routes_within_budget=stats['routes_within_budget'],
            compliance_rate=stats['budget_compliance_rate']
        ))
        
        if self.best_cheap["route"]:
            within_budget = self._is_within_budget(self.best_cheap["cost"])
            status = "✅ DANS LE BUDGET" if within_budget else "❌ HORS BUDGET"
            print(BudgetMessages.BEST_CHEAP_ROUTE.format(
                toll_count=self.best_cheap['toll_count'],
                cost=self.best_cheap['cost'],
                duration=self.best_cheap['duration']/60,
                status=status
            ))
        else:
            print(CommonMessages.NO_ECONOMIC_ROUTE)
            
        if self.best_fast["route"]:
            within_budget = self._is_within_budget(self.best_fast["cost"])
            status = "✅ DANS LE BUDGET" if within_budget else "❌ HORS BUDGET"
            print(BudgetMessages.BEST_FAST_ROUTE.format(
                toll_count=self.best_fast['toll_count'],
                cost=self.best_fast['cost'],
                duration=self.best_fast['duration']/60,
                status=status
            ))
        else:
            print(CommonMessages.NO_FAST_ROUTE)
            
        if self.best_min_tolls["route"]:
            within_budget = self._is_within_budget(self.best_min_tolls["cost"])
            status = "✅ DANS LE BUDGET" if within_budget else "❌ HORS BUDGET"
            print(BudgetMessages.BEST_MIN_TOLLS_ROUTE.format(
                toll_count=self.best_min_tolls['toll_count'],
                cost=self.best_min_tolls['cost'],
                duration=self.best_min_tolls['duration']/60,
                status=status
            ))
        else:
            print(CommonMessages.NO_MIN_TOLLS_ROUTE)