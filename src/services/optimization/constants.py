"""
constants.py
-----------

Configuration constants for toll optimization strategies.
Centralise toutes les valeurs magiques pour faciliter la maintenance.
"""

import os
from src.services.common.base_constants import BaseOptimizationConfig

class TollOptimizationConfig(BaseOptimizationConfig):
    """Configuration constants for toll route optimization."""
    
    # === Cost optimization ===
    EARLY_STOP_ZERO_COST = True  # Arrêt anticipé si coût nul trouvé
    UNLIMITED_BASE_COST = float('inf')  # Coût de base illimité pour certains cas
    
    # === Toll detection configuration ===
    TOLL_DETECTION_BUFFER_M = 80.0  # Buffer pour détecter les péages (50m au lieu de 120m)
      # === Performance tracking operation names ===
    class Operations:
        """Noms standardisés des opérations pour le tracking de performance."""
        
        # Main operations
        COMPUTE_ROUTE_WITH_TOLL_LIMIT = "compute_route_with_toll_limit"
        COMPUTE_ROUTE_NO_TOLL = "compute_route_no_toll"
        COMPUTE_ROUTE_ONE_OPEN_TOLL = "compute_route_with_one_open_toll"
        COMPUTE_ROUTE_MANY_TOLLS = "compute_route_with_many_tolls"
        
        # ORS API calls
        ORS_BASE_ROUTE = "ORS_base_route"
        ORS_AVOID_TOLLWAYS = "ORS_avoid_tollways"  
        ORS_ALTERNATIVE_ROUTE = "ORS_alternative_route"
        
        # Toll operations
        LOCATE_TOLLS = "locate_tolls"
        LOCATE_TOLLS_NO_TOLL = "locate_tolls_no_toll"
        LOCATE_TOLLS_ONE_TOLL = "locate_tolls_one_toll"
        LOCATE_TOLLS_MANY_TOLLS = "locate_tolls_many_tolls"
        LOCATE_TOLLS_FALLBACK = "locate_tolls_fallback"
        
        # Combination testing
        PREPARE_TOLL_COMBINATIONS = "prepare_toll_combinations"
        TEST_TOLL_COMBINATIONS = "test_toll_combinations"
        TEST_SINGLE_COMBINATION = "test_single_combination"
        CREATE_AVOIDANCE_POLYGON = "create_avoidance_polygon"
        
        # Route analysis
        ANALYZE_ALTERNATIVE_ROUTE = "analyze_alternative_route"
        MERGE_ROUTES = "merge_routes"
        CALCULATE_FINAL_METRICS = "calculate_final_metrics"
        
        # Strategy operations
        HANDLE_NO_TOLL_ROUTE = "handle_no_toll_route"
        HANDLE_ONE_TOLL_ROUTE = "handle_one_toll_route"
        GET_FALLBACK_ROUTE = "get_fallback_route"
        HANDLE_TOLL_FAILURE = "handle_toll_failure"
        
        # Utility operations
        FILTER_OPEN_TOLLS = "filter_open_tolls"
        GET_ALL_OPEN_TOLLS = "get_all_open_tolls"
        GET_BASE_METRICS = "get_base_metrics"