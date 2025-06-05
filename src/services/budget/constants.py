"""
constants.py
-----------

Configuration constants for budget optimization strategies.
Centralise toutes les valeurs magiques pour faciliter la maintenance.
"""

class BudgetOptimizationConfig:
    """Configuration constants for budget route optimization."""
    
    # === Distance and proximity limits ===
    MAX_DISTANCE_SEARCH_M = 100000  # 100km pour la recherche de péages à proximité
    MAX_FALLBACK_COMBINATIONS = 50  # Limite pour éviter trop de calculs en fallback
    
    # === File paths ===
    BARRIERS_CSV_PATH = "data/barriers.csv"  # Chemin vers les données de péages
    
    # === Route calculation defaults ===
    DEFAULT_VEH_CLASS = "c1"
    DEFAULT_MAX_COMB_SIZE = 2
    
    # === Budget validation limits ===
    MIN_BUDGET_PERCENT = 0.0    # 0%
    MAX_BUDGET_PERCENT = 1.0    # 100%
    MIN_ABSOLUTE_BUDGET = 0     # 0€
    
    # === Performance tracking operation names ===
    class Operations:
        # Main operations
        COMPUTE_ROUTE_WITH_BUDGET_LIMIT = "compute_route_with_budget_limit"
        COMPUTE_ROUTE_ZERO_BUDGET = "compute_route_zero_budget"
        COMPUTE_ROUTE_PERCENTAGE_BUDGET = "compute_route_percentage_budget"
        COMPUTE_ROUTE_ABSOLUTE_BUDGET = "compute_route_absolute_budget"
        
        # Budget-specific operations
        HANDLE_ZERO_BUDGET_ROUTE = "handle_zero_budget_route"
        HANDLE_PERCENTAGE_BUDGET_ROUTE = "handle_percentage_budget_route"
        HANDLE_ABSOLUTE_BUDGET_ROUTE = "handle_absolute_budget_route"
        HANDLE_BUDGET_FAILURE = "handle_budget_failure"
        
        # Base metrics operations
        GET_BASE_METRICS_PERCENTAGE = "get_base_metrics_percentage"
        GET_BASE_METRICS_ABSOLUTE = "get_base_metrics_absolute"
        
        # Optimization operations
        OPTIMIZE_PERCENTAGE_BUDGET = "optimize_percentage_budget"
        OPTIMIZE_ABSOLUTE_BUDGET = "optimize_absolute_budget"
        
        # Fallback operations
        ZERO_BUDGET_FALLBACK = "zero_budget_fallback"
        ABSOLUTE_BUDGET_FALLBACK = "absolute_budget_fallback"
        PERCENTAGE_BUDGET_FALLBACK = "percentage_budget_fallback"
        GENERAL_FALLBACK = "general_fallback"
        SEARCH_FREE_ROUTES = "search_free_routes"
        FIND_ABSOLUTE_CHEAPEST = "find_absolute_cheapest"
        FIND_CLOSEST_TO_BUDGET = "find_closest_to_budget"
        FIND_FASTEST_AMONG_CHEAPEST = "find_fastest_among_cheapest"
        
        # Toll location operations
        LOCATE_TOLLS_ZERO_BUDGET = "locate_tolls_zero_budget"
        LOCATE_TOLLS_PERCENTAGE_BUDGET = "locate_tolls_percentage_budget"
        LOCATE_TOLLS_ABSOLUTE_BUDGET = "locate_tolls_absolute_budget"
        
        # Testing operations
        TEST_INDIVIDUAL_TOLLS_PERCENTAGE = "test_individual_tolls_percentage"
        TEST_COMBINATIONS_PERCENTAGE = "test_combinations_percentage"
        TEST_PROMISING_TOLLS_ABSOLUTE = "test_promising_tolls_absolute"
        TEST_INDIVIDUAL_TOLLS_ABSOLUTE = "test_individual_tolls_absolute"
        TEST_COMBINATIONS_ABSOLUTE = "test_combinations_absolute"
        
        # Analysis operations
        ANALYZE_ALTERNATIVE_PERCENTAGE = "analyze_alternative_percentage"
        ANALYZE_COMBINATION_PERCENTAGE = "analyze_combination_percentage"
        ANALYZE_ALTERNATIVE_ABSOLUTE = "analyze_alternative_absolute"
        ANALYZE_COMBINATION_ABSOLUTE = "analyze_combination_absolute"
        
        # Error handling
        GET_BASE_ROUTE_FALLBACK = "get_base_route_fallback"
    
    # === Status codes ===
    class StatusCodes:
        # Success codes
        BUDGET_ZERO_NO_TOLL_SUCCESS = "BUDGET_ZERO_NO_TOLL_SUCCESS"
        BUDGET_ALREADY_SATISFIED = "BUDGET_ALREADY_SATISFIED"
        BUDGET_SATISFIED = "BUDGET_SATISFIED"
        FREE_ALTERNATIVE_FOUND = "FREE_ALTERNATIVE_FOUND"
        FASTEST_AMONG_CHEAPEST_FOUND = "FASTEST_AMONG_CHEAPEST_FOUND"
        CLOSEST_TO_BUDGET_FOUND = "CLOSEST_TO_BUDGET_FOUND"
        EXPANDED_BUDGET_SATISFIED = "EXPANDED_BUDGET_SATISFIED"
        
        # Warning codes
        BUDGET_ZERO_SOME_TOLLS_PRESENT = "BUDGET_ZERO_SOME_TOLLS_PRESENT"
        ONLY_CHEAPEST_FOUND = "ONLY_CHEAPEST_FOUND"
        
        # Error codes
        NO_ROUTE_WITHIN_BUDGET = "NO_ROUTE_WITHIN_BUDGET"
        NO_ROUTE_WITHIN_BUDGET_RETURNING_FASTEST_AMONG_CHEAPEST = "NO_ROUTE_WITHIN_BUDGET_RETURNING_FASTEST_AMONG_CHEAPEST"
        NO_TOLLS_FOUND = "NO_TOLLS_FOUND"
        NO_ALTERNATIVE_FOUND = "NO_ALTERNATIVE_FOUND"
        FALLBACK_BASE_ROUTE_USED = "FALLBACK_BASE_ROUTE_USED"
        CRITICAL_ERROR = "CRITICAL_ERROR"
        ORS_CONNECTION_ERROR = "ORS_CONNECTION_ERROR"
        INVALID_MAX_PRICE = "INVALID_MAX_PRICE"
        INVALID_MAX_PRICE_PERCENT = "INVALID_MAX_PRICE_PERCENT"
    
    # === Messages ===
    class Messages:
        # Search messages
        SEARCH_ZERO_BUDGET = "Recherche d'un itinéraire avec budget zéro..."
        SEARCH_PERCENTAGE_BUDGET = "Recherche d'un itinéraire avec budget à {percent}% du coût de base..."
        SEARCH_ABSOLUTE_BUDGET = "Recherche d'un itinéraire avec budget maximum de {budget}€..."
        
        # Progress messages
        PROGRESS_COMBINATIONS = "Progression: {count} combinaisons testées"
        FOUND_SOLUTION_WITHIN_BUDGET = "Solution trouvée dans le budget: {cost}€ ≤ {limit}€"
        NO_SOLUTION_WITHIN_BUDGET = "Aucune solution dans le budget. Meilleure solution: {cost}€ > {limit}€"
        
        # Base route messages
        BASE_ROUTE_COST = "Coût de base: {cost}€"
        BUDGET_LIMIT = "Limite budgétaire: {limit}€"
        BUDGET_GAP = "Écart budgétaire à combler: {gap}€"
        
        # Toll testing messages
        TEST_INDIVIDUAL_TOLLS = "Test de l'évitement des péages individuels..."
        TEST_COMBINATIONS = "Test des combinaisons de péages..."
        TEST_PROMISING_TOLLS = "Test prioritaire des péages les plus prometteurs..."
        
        # Results messages
        ROUTE_ALTERNATIVE = "Route alternative: coût={cost}€, durée={duration:.1f}min"
        ROUTE_GRATUITE_TROUVEE = "Route gratuite trouvée !"
        SOLUTION_PROMETTEUSE = "Solution prometteuse trouvée dans le budget: {cost}€ ≤ {limit}€"
        
        # Validation errors
        ATTENTION_TOLLS_PRESENT = "Attention: l'itinéraire sans péage contient quand même {count} péages"
        IMPOSSIBLE_NO_TOLL_ROUTE = "Impossible de trouver un itinéraire sans péage: {error}"
        
        # Fallback messages
        FALLBACK_ZERO_BUDGET = "Fallback budget zéro : recherche d'alternatives gratuites ou peu chères..."
        FALLBACK_ABSOLUTE_BUDGET = "Fallback budget absolu : recherche d'alternatives proches de {budget}€..."
        FALLBACK_PERCENTAGE_BUDGET = "Fallback budget pourcentage : recherche d'alternatives pour {percent}%..."
        FALLBACK_GENERAL = "Fallback général : recherche de la meilleure solution globale..."
        
        # Strategy delegation messages
        STRATEGY_ZERO_SELECTED = "Stratégie budget zéro sélectionnée"
        STRATEGY_PERCENTAGE_SELECTED = "Stratégie budget pourcentage sélectionnée ({percent}%)"
        STRATEGY_ABSOLUTE_SELECTED = "Stratégie budget absolu sélectionnée ({budget}€)"
        STRATEGY_FALLBACK_SELECTED = "Stratégie de fallback sélectionnée"
        
        # Error handling messages
        VALIDATION_FAILED = "Échec de la validation des paramètres"
        STRATEGY_FAILED = "Échec de la stratégie principale, activation du fallback"
        CRITICAL_ERROR_OCCURRED = "Erreur critique détectée: {error}"
    
    @staticmethod
    def get_barriers_csv_path():
        """Retourne le chemin vers le fichier des barrières."""
        return BudgetOptimizationConfig.BARRIERS_CSV_PATH
    
    @staticmethod
    def validate_percentage(percentage):
        """Valide qu'un pourcentage est dans les limites autorisées."""
        return (BudgetOptimizationConfig.MIN_BUDGET_PERCENT <= 
                percentage <= 
                BudgetOptimizationConfig.MAX_BUDGET_PERCENT)
    
    @staticmethod
    def validate_absolute_budget(budget):
        """Valide qu'un budget absolu est valide."""
        return budget >= BudgetOptimizationConfig.MIN_ABSOLUTE_BUDGET