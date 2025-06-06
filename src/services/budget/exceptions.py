"""
exceptions.py
------------

Exceptions personnalisées pour l'optimisation budgétaire.
Responsabilité unique : définir une hiérarchie d'exceptions métier budgétaire.
"""

from src.services.toll.exceptions import TollOptimizationError
from src.services.budget.constants import BudgetOptimizationConfig as Config


class BudgetOptimizationError(TollOptimizationError):
    """Exception de base pour les erreurs d'optimisation budgétaire."""
    
    def __init__(self, message, status_code=None, budget_context=None):
        super().__init__(message, status_code)
        self.budget_context = budget_context


class BudgetExceededError(BudgetOptimizationError):
    """Le coût dépasse la limite budgétaire."""
    
    def __init__(self, cost, budget_limit, budget_type="absolute"):
        message = f"Coût {cost}€ dépasse la limite budgétaire de {budget_limit}€"
        super().__init__(message, status_code=Config.StatusCodes.NO_ROUTE_WITHIN_BUDGET)
        self.cost = cost
        self.budget_limit = budget_limit
        self.budget_type = budget_type


class InvalidBudgetError(BudgetOptimizationError):
    """Contrainte budgétaire invalide."""
    
    def __init__(self, budget_value, budget_type):
        message = f"Contrainte budgétaire invalide: {budget_type}={budget_value}"
        
        # Déterminer le code de statut selon le type
        if budget_type == "absolute":
            status_code = Config.StatusCodes.INVALID_MAX_PRICE
        elif budget_type == "percentage":
            status_code = Config.StatusCodes.INVALID_MAX_PRICE_PERCENT
        else:
            status_code = Config.StatusCodes.CRITICAL_ERROR
        
        super().__init__(message, status_code=status_code)
        self.budget_value = budget_value
        self.budget_type = budget_type


class NoRouteWithinBudgetError(BudgetOptimizationError):
    """Aucune route trouvée respectant le budget."""
    
    def __init__(self, budget_limit, best_cost=None, budget_type="absolute"):
        if best_cost is not None:
            message = f"Aucune route dans le budget {budget_limit}€. Meilleur coût: {best_cost}€"
        else:
            message = f"Aucune route trouvée dans le budget {budget_limit}€"
        
        super().__init__(message, status_code=Config.StatusCodes.NO_ROUTE_WITHIN_BUDGET)
        self.budget_limit = budget_limit
        self.best_cost = best_cost
        self.budget_type = budget_type


class ZeroBudgetError(BudgetOptimizationError):
    """Erreur spécifique aux contraintes de budget zéro."""
    
    def __init__(self, message="Aucune route gratuite trouvée", toll_count=0):
        super().__init__(message, status_code=Config.StatusCodes.BUDGET_ZERO_SOME_TOLLS_PRESENT)
        self.toll_count = toll_count


class PercentageBudgetError(BudgetOptimizationError):
    """Erreur spécifique aux contraintes de budget en pourcentage."""
    
    def __init__(self, percentage, base_cost, actual_limit):
        message = f"Budget {percentage*100}% du coût de base ({base_cost}€) = {actual_limit}€ non respecté"
        super().__init__(message, status_code=Config.StatusCodes.NO_ROUTE_WITHIN_BUDGET)
        self.percentage = percentage
        self.base_cost = base_cost
        self.actual_limit = actual_limit


class BudgetStrategyError(BudgetOptimizationError):
    """Erreur dans l'exécution d'une stratégie budgétaire."""
    
    def __init__(self, strategy_name, original_exception):
        message = f"Stratégie {strategy_name} échouée: {original_exception}"
        super().__init__(message, status_code=Config.StatusCodes.CRITICAL_ERROR)
        self.strategy_name = strategy_name
        self.original_exception = original_exception


class BudgetFallbackError(BudgetOptimizationError):
    """Erreur dans l'exécution du fallback budgétaire."""
    
    def __init__(self, fallback_type, original_exception):
        message = f"Fallback {fallback_type} échoué: {original_exception}"
        super().__init__(message, status_code=Config.StatusCodes.NO_ALTERNATIVE_FOUND)
        self.fallback_type = fallback_type
        self.original_exception = original_exception


class BudgetValidationError(BudgetOptimizationError):
    """Erreur de validation des paramètres budgétaires."""
    
    def __init__(self, parameter_name, parameter_value, validation_message):
        message = f"Validation échouée pour {parameter_name}={parameter_value}: {validation_message}"
        super().__init__(message, status_code=Config.StatusCodes.INVALID_MAX_PRICE)
        self.parameter_name = parameter_name
        self.parameter_value = parameter_value
        self.validation_message = validation_message