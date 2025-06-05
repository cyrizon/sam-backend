"""
error_handler.py
---------------

Gestion centralisée des erreurs pour l'optimisation budgétaire.
"""

from src.services.toll.error_handler import ErrorHandler as BaseErrorHandler
from src.services.toll.result_formatter import ResultFormatter


class BudgetErrorHandler(BaseErrorHandler):
    """Gestionnaire d'erreurs spécialisé pour l'optimisation budgétaire."""
    
    @staticmethod
    def handle_budget_validation_error(max_price, max_price_percent):
        """Gère les erreurs de validation des contraintes budgétaires."""
        if max_price is not None and max_price < 0:
            return ResultFormatter.format_optimization_results(
                fastest=None,
                cheapest=None,
                min_tolls=None,
                status="INVALID_MAX_PRICE"
            )
        
        if max_price_percent is not None and (max_price_percent < 0 or max_price_percent > 1):
            return ResultFormatter.format_optimization_results(
                fastest=None,
                cheapest=None,
                min_tolls=None,
                status="INVALID_MAX_PRICE_PERCENT"
            )
        
        return None
    
    @staticmethod
    def handle_no_budget_route_error(price_limit, base_cost):
        """Gère le cas où aucune route ne respecte le budget."""
        return ResultFormatter.format_optimization_results(
            fastest=None,
            cheapest=None,
            min_tolls=None,
            status="NO_ROUTE_WITHIN_BUDGET"
        )