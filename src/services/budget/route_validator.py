"""
route_validator.py
-----------------

Validateur centralisé pour les contraintes budgétaires sur les routes.
Responsabilité unique : valider que les routes respectent les contraintes budgétaires.
"""

from src.services.budget.constants import BudgetOptimizationConfig as Config


class BudgetRouteValidator:
    """Validateur centralisé pour les contraintes budgétaires."""
    
    @staticmethod
    def validate_budget_limit(cost, budget_limit, operation_name=""):
        """
        Vérifie que le coût respecte la limite budgétaire.
        
        Args:
            cost: Coût de la route
            budget_limit: Limite budgétaire
            operation_name: Nom de l'opération pour le logging
            
        Returns:
            bool: True si le coût respecte la limite
        """
        if cost > budget_limit:
            operation_info = f" pour {operation_name}" if operation_name else ""
            print(f"Route ignorée : coût {cost}€ > limite {budget_limit}€" + operation_info)
            return False
        return True
    
    @staticmethod
    def validate_percentage_budget(cost, base_cost, percentage_limit, operation_name=""):
        """
        Vérifie que le coût respecte le pourcentage du coût de base.
        
        Args:
            cost: Coût de la route
            base_cost: Coût de base de référence
            percentage_limit: Limite en pourcentage (0.8 = 80%)
            operation_name: Nom de l'opération pour le logging
            
        Returns:
            bool: True si le coût respecte la limite
        """
        price_limit = base_cost * percentage_limit
        return BudgetRouteValidator.validate_budget_limit(cost, price_limit, operation_name)
    
    @staticmethod
    def validate_zero_budget(cost, operation_name=""):
        """
        Vérifie que le coût est zéro (route gratuite).
        
        Args:
            cost: Coût de la route
            operation_name: Nom de l'opération pour le logging
            
        Returns:
            bool: True si la route est gratuite
        """
        return BudgetRouteValidator.validate_budget_limit(cost, 0, operation_name)
    
    @staticmethod
    def is_within_budget(route_result, budget_limit):
        """
        Vérifie si un résultat de route respecte le budget.
        
        Args:
            route_result: Résultat de route formaté
            budget_limit: Limite budgétaire
            
        Returns:
            bool: True si la route respecte le budget
        """
        if not route_result or route_result.get("route") is None:
            return False
        return route_result.get("cost", float('inf')) <= budget_limit
    
    @staticmethod
    def get_best_within_budget(results, budget_limit):
        """
        Retourne le meilleur résultat respectant le budget.
        
        Args:
            results: Dictionnaire des résultats (fastest, cheapest, min_tolls)
            budget_limit: Limite budgétaire
            
        Returns:
            dict ou None: Meilleur résultat dans le budget ou None
        """
        candidates = []
        
        for result_type, result in results.items():
            if BudgetRouteValidator.is_within_budget(result, budget_limit):
                candidates.append((result_type, result))
        
        if not candidates:
            return None
        
        # Prioriser par ordre : fastest, cheapest, min_tolls
        priority_order = ["fastest", "cheapest", "min_tolls"]
        for priority in priority_order:
            for result_type, result in candidates:
                if result_type == priority:
                    return result
        
        return candidates[0][1]  # Fallback au premier disponible
    
    @staticmethod
    def filter_results_by_budget(results, budget_limit):
        """
        Filtre les résultats pour ne garder que ceux respectant le budget.
        
        Args:
            results: Dictionnaire des résultats
            budget_limit: Limite budgétaire
            
        Returns:
            dict: Résultats filtrés
        """
        filtered = {}
        
        for result_type, result in results.items():
            if BudgetRouteValidator.is_within_budget(result, budget_limit):
                filtered[result_type] = result
            else:
                filtered[result_type] = None
        
        return filtered
    
    @staticmethod
    def validate_budget_parameters(max_price, max_price_percent):
        """
        Valide les paramètres de contrainte budgétaire.
        
        Args:
            max_price: Budget maximum en euros
            max_price_percent: Budget en pourcentage
            
        Returns:
            tuple: (is_valid, error_message)
        """
        # Vérifier qu'au moins un paramètre est fourni
        if max_price is None and max_price_percent is None:
            return True, None  # Pas de contrainte = valide
        
        # Vérifier qu'un seul paramètre est fourni
        if max_price is not None and max_price_percent is not None:
            return False, "Impossible de spécifier à la fois max_price et max_price_percent"
        
        # Valider le budget absolu
        if max_price is not None:
            if not Config.validate_absolute_budget(max_price):
                return False, f"Budget absolu invalide: {max_price}€ (minimum: {Config.MIN_ABSOLUTE_BUDGET}€)"
        
        # Valider le budget pourcentage
        if max_price_percent is not None:
            if not Config.validate_percentage(max_price_percent):
                return False, f"Budget pourcentage invalide: {max_price_percent*100}% (plage: {Config.MIN_BUDGET_PERCENT*100}%-{Config.MAX_BUDGET_PERCENT*100}%)"
        
        return True, None
    
    @staticmethod
    def get_budget_info(max_price, max_price_percent, base_cost=None):
        """
        Retourne des informations formatées sur la contrainte budgétaire.
        
        Args:
            max_price: Budget maximum en euros
            max_price_percent: Budget en pourcentage
            base_cost: Coût de base (nécessaire pour les pourcentages)
            
        Returns:
            dict: Informations sur le budget
        """
        if max_price == 0 or max_price_percent == 0:
            return {
                "type": "zero",
                "limit": 0,
                "description": "Budget zéro (routes gratuites uniquement)"
            }
        elif max_price_percent is not None:
            if base_cost is not None:
                actual_limit = base_cost * max_price_percent
                return {
                    "type": "percentage",
                    "limit": actual_limit,
                    "percentage": max_price_percent,
                    "base_cost": base_cost,
                    "description": f"{max_price_percent*100}% du coût de base ({base_cost}€) = {actual_limit}€"
                }
            else:
                return {
                    "type": "percentage",
                    "limit": None,
                    "percentage": max_price_percent,
                    "description": f"{max_price_percent*100}% du coût de base (non calculé)"
                }
        elif max_price is not None:
            return {
                "type": "absolute",
                "limit": max_price,
                "description": f"Budget maximum {max_price}€"
            }
        else:
            return {
                "type": "none",
                "limit": None,
                "description": "Aucune contrainte budgétaire"
            }