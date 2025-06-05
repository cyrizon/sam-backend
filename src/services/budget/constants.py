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
    MAX_DISTANCE_SEARCH_M = 100000  # 100km

    # === File paths ===
    BARRIERS_CSV_PATH = "data/barriers.csv"  # Chemin vers les données de péages
    
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
        
        # Opérations pour pourcentage
        COMPUTE_ROUTE_PERCENTAGE_BUDGET = "compute_route_percentage_budget"
        HANDLE_PERCENTAGE_BUDGET_ROUTE = "handle_percentage_budget_route"
        GET_BASE_METRICS_PERCENTAGE = "get_base_metrics_percentage"
        LOCATE_TOLLS_PERCENTAGE_BUDGET = "locate_tolls_percentage_budget"
        OPTIMIZE_PERCENTAGE_BUDGET = "optimize_percentage_budget"
        TEST_INDIVIDUAL_TOLLS_PERCENTAGE = "test_individual_tolls_percentage"
        TEST_COMBINATIONS_PERCENTAGE = "test_combinations_percentage"
        ANALYZE_ALTERNATIVE_PERCENTAGE = "analyze_alternative_percentage"
        ANALYZE_COMBINATION_PERCENTAGE = "analyze_combination_percentage"
        
        # Opérations pour budget absolu
        COMPUTE_ROUTE_ABSOLUTE_BUDGET = "compute_route_absolute_budget"
        HANDLE_ABSOLUTE_BUDGET_ROUTE = "handle_absolute_budget_route"
        GET_BASE_METRICS_ABSOLUTE = "get_base_metrics_absolute"
        LOCATE_TOLLS_ABSOLUTE_BUDGET = "locate_tolls_absolute_budget"
        OPTIMIZE_ABSOLUTE_BUDGET = "optimize_absolute_budget"
        TEST_PROMISING_TOLLS_ABSOLUTE = "test_promising_tolls_absolute"
        TEST_INDIVIDUAL_TOLLS_ABSOLUTE = "test_individual_tolls_absolute"
        TEST_COMBINATIONS_ABSOLUTE = "test_combinations_absolute"
        ANALYZE_ALTERNATIVE_ABSOLUTE = "analyze_alternative_absolute"
        ANALYZE_COMBINATION_ABSOLUTE = "analyze_combination_absolute"
    
    @staticmethod
    def get_barriers_csv_path():
        """Retourne le chemin vers le fichier des barrières."""
        return BudgetOptimizationConfig.BARRIERS_CSV_PATH