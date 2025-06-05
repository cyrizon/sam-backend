"""
error_handler.py
---------------

Gestion centralisée des erreurs pour l'optimisation budgétaire.
"""

from src.services.toll.error_handler import ErrorHandler as BaseErrorHandler


class BudgetErrorHandler(BaseErrorHandler):
    """Gestionnaire d'erreurs spécialisé pour l'optimisation budgétaire."""
    
    @staticmethod
    def handle_budget_validation_error(max_price, max_price_percent):
        """Gère les erreurs de validation des contraintes budgétaires."""
        if max_price is not None and max_price < 0:
            return {
                "fastest": None,
                "cheapest": None,
                "status": "INVALID_MAX_PRICE",
                "error": f"Le prix maximum ne peut pas être négatif: {max_price}"
            }
        
        if max_price_percent is not None and (max_price_percent < 0 or max_price_percent > 1):
            return {
                "fastest": None,
                "cheapest": None,
                "status": "INVALID_MAX_PRICE_PERCENT",
                "error": f"Le pourcentage doit être entre 0 et 1: {max_price_percent}"
            }
        
        return None
    
    @staticmethod
    def handle_no_budget_route_error(price_limit, base_cost):
        """Gère le cas où aucune route ne respecte le budget."""
        return {
            "fastest": None,
            "cheapest": None,
            "status": "NO_ROUTE_WITHIN_BUDGET",
            "error": f"Aucune route trouvée respectant le budget de {price_limit}€ (coût de base: {base_cost}€)"
        }