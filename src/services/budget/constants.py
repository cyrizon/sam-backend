"""
constants.py
-----------

Constantes et configuration pour l'optimisation budgétaire.
"""

class BudgetOptimizationConfig:
    """Configuration centralisée pour l'optimisation budgétaire."""
    
    # Valeurs par défaut
    DEFAULT_VEH_CLASS = "c1"
    DEFAULT_MAX_COMB_SIZE = 2
    
    # Codes de statut (cohérents avec le format toll)
    class StatusCodes:
        BUDGET_ZERO_NO_TOLL_SUCCESS = "BUDGET_ZERO_NO_TOLL_SUCCESS"
        BUDGET_ZERO_SOME_TOLLS_PRESENT = "BUDGET_ZERO_SOME_TOLLS_PRESENT"
        BUDGET_ALREADY_SATISFIED = "BUDGET_ALREADY_SATISFIED"
        BUDGET_SATISFIED = "BUDGET_SATISFIED"
        NO_ROUTE_WITHIN_BUDGET = "NO_ROUTE_WITHIN_BUDGET"
        NO_ROUTE_WITHIN_BUDGET_RETURNING_FASTEST_AMONG_CHEAPEST = "NO_ROUTE_WITHIN_BUDGET_RETURNING_FASTEST_AMONG_CHEAPEST"
        NO_TOLLS_FOUND = "NO_TOLLS_FOUND"
        ORS_CONNECTION_ERROR = "ORS_CONNECTION_ERROR"
    
    # Messages d'information
    class Messages:
        SEARCH_ZERO_BUDGET = "Recherche d'un itinéraire avec budget zéro..."
        ATTENTION_TOLLS_PRESENT = "Attention: l'itinéraire sans péage contient quand même {count} péages"
        IMPOSSIBLE_NO_TOLL_ROUTE = "Impossible de trouver un itinéraire sans péage: {error}"
    
    # Noms d'opérations pour le tracking
    class Operations:
        COMPUTE_ROUTE_WITH_BUDGET_LIMIT = "compute_route_with_budget_limit"
        COMPUTE_ROUTE_ZERO_BUDGET = "compute_route_zero_budget"
        HANDLE_ZERO_BUDGET_ROUTE = "handle_zero_budget_route"
        LOCATE_TOLLS_ZERO_BUDGET = "locate_tolls_zero_budget"