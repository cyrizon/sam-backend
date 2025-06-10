"""
constants.py
-----------

Configuration constants for budget optimization strategies.
Centralise toutes les valeurs magiques pour faciliter la maintenance.
"""

from src.services.common.base_constants import BaseOptimizationConfig

class BudgetOptimizationConfig(BaseOptimizationConfig):
    """Configuration constants for budget route optimization."""
      # === Budget-specific limits ===
    MAX_FALLBACK_COMBINATIONS = 50  # Limite pour éviter trop de calculs en fallback
    
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