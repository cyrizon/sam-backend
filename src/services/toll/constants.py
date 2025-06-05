"""
constants.py
-----------

Configuration constants for toll optimization strategies.
Centralise toutes les valeurs magiques pour faciliter la maintenance.
"""

import os

class TollOptimizationConfig:
    """Configuration constants for toll route optimization."""
    
    # === Distance and proximity limits ===
    MAX_DISTANCE_SEARCH_M = 100000  # 100 km - Distance maximale pour chercher des péages
    MAX_NEARBY_TOLLS_TO_TEST = 10   # Nombre maximum de péages proches à tester
    
    # === Performance and progress thresholds ===
    COMBINATION_PROGRESS_INTERVAL = 10  # Affichage du progrès toutes les N combinaisons
    
    # === File paths ===
    BARRIERS_CSV_PATH = "data/barriers.csv"  # Chemin vers les données de péages
    
    # === Cost optimization ===
    EARLY_STOP_ZERO_COST = True  # Arrêt anticipé si coût nul trouvé
    UNLIMITED_BASE_COST = float('inf')  # Coût de base illimité pour certains cas
    
    # === Route calculation defaults ===
    DEFAULT_MAX_COMB_SIZE = 2  # Taille max par défaut des combinaisons
    DEFAULT_VEH_CLASS = "c1"   # Classe de véhicule par défaut
    
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
        
        # Utility operations
        FILTER_OPEN_TOLLS = "filter_open_tolls"
        GET_ALL_OPEN_TOLLS = "get_all_open_tolls"
        GET_BASE_METRICS = "get_base_metrics"
    
    # === Status codes ===
    class StatusCodes:
        """Status codes standardisés pour les résultats."""
        
        # Success codes
        NO_TOLL_SUCCESS = "NO_TOLL_SUCCESS"
        ONE_OPEN_TOLL_SUCCESS = "ONE_OPEN_TOLL_SUCCESS"
        MULTI_TOLL_SUCCESS = "MULTI_TOLL_SUCCESS"
        GENERAL_STRATEGY = "GENERAL_STRATEGY"
        GENERAL_STRATEGY_WITH_MIN_TOLLS = "GENERAL_STRATEGY_WITH_MIN_TOLLS"
        MINIMUM_TOLLS_SOLUTION = "MINIMUM_TOLLS_SOLUTION"
        
        # Warning codes
        SOME_TOLLS_PRESENT = "SOME_TOLLS_PRESENT"
        
        # Error codes
        NO_TOLL_ROUTE_NOT_POSSIBLE = "NO_TOLL_ROUTE_NOT_POSSIBLE"
        NO_OPEN_TOLL_FOUND = "NO_OPEN_TOLL_FOUND"
        NO_VALID_OPEN_TOLL_ROUTE = "NO_VALID_OPEN_TOLL_ROUTE"
        NO_VALID_ROUTE_WITH_MAX_TOLLS = "NO_VALID_ROUTE_WITH_MAX_TOLLS"
        NO_VALID_ROUTE_WITH_MAX_ONE_TOLL = "NO_VALID_ROUTE_WITH_MAX_ONE_TOLL"
        ORS_CONNECTION_ERROR = "ORS_CONNECTION_ERROR"
    
    # === Logging messages ===
    class Messages:
        """Messages standardisés pour les logs."""
        
        SEARCH_NO_TOLL = "Recherche d'un itinéraire sans péage..."
        SEARCH_ONE_OPEN_TOLL = "Recherche d'un itinéraire avec un seul péage ouvert..."
        SEARCH_MANY_TOLLS = "Recherche d'itinéraires avec max {max_tolls} péages..."
        
        FOUND_OPEN_TOLLS_NEARBY = "Trouvé {count} péages ouverts à proximité immédiate"
        FOUND_OPEN_TOLLS_NETWORK = "Trouvé {count} péages ouverts dans un rayon de {distance:.1f} km"
        
        NO_OPEN_TOLLS_NEARBY = "Aucune solution trouvée avec les péages ouverts à proximité. Test avec tous les péages ouverts du réseau..."
        NO_OPEN_TOLLS_IN_RADIUS = "Aucun péage à système ouvert trouvé dans un rayon de {distance:.1f} km"
        
        PROGRESS_COMBINATIONS = "Progression: {count} combinaisons testées"
        
        SOLUTION_ONE_TOLL = "Solution avec exactement 1 péage: péage={toll_id}, coût={cost}€, durée={duration:.1f}min"
        SOLUTION_MULTIPLE_TOLLS = "Solution avec {toll_count} péages: péage principal={toll_id}, coût={cost}€, durée={duration:.1f}min"
        
        NO_EXACT_ONE_TOLL = "Pas de solution avec exactement un péage ouvert, mais trouvé une solution avec {toll_count} péages"
        
        TOLLS_ON_ROUTE = "Péages sur la route :"
        TOLLS_NEARBY = "Péages proches :"
        
        ROUTE_IGNORED_MAX_TOLLS = "Itinéraire ignoré : {toll_count} péages > max_tolls={max_tolls}"
        AVOIDED_TOLLS_STILL_PRESENT = "Attention : certains péages à éviter sont toujours présents : {present_tolls}"
        IMPOSSIBLE_AVOID_TOLLS = "Impossible d'éviter les péages indésirables sur {part_name}: {unwanted_ids}"
        TARGET_TOLL_MISSING = "Le péage cible {toll_id} n'est pas présent dans l'itinéraire final"
        
        NO_ROUTE_FOUND_MAX_TOLLS = "Aucun itinéraire trouvé respectant la contrainte de max_tolls"
        
        # Results logging
        RESULT_BASE = "[RESULT] Base: {toll_count} péages, coût={cost}€, durée={duration:.1f} min"
        RESULT_CHEAPEST = "[RESULT] Cheapest: {toll_count} péages, coût={cost}€, durée={duration:.1f} min"
        RESULT_FASTEST = "[RESULT] Fastest: {toll_count} péages, coût={cost}€, durée={duration:.1f} min"
        RESULT_MIN_TOLLS = "[RESULT] Minimum tolls: {toll_count} péages, coût={cost}€, durée={duration:.1f} min"
        
        NO_ECONOMIC_ROUTE = "[RESULT] Pas d'itinéraire économique trouvé respectant la contrainte de max_tolls"
        NO_FAST_ROUTE = "[RESULT] Pas d'itinéraire rapide trouvé respectant la contrainte de max_tolls"
        NO_MIN_TOLLS_ROUTE = "[RESULT] Pas d'itinéraire avec un minimum de péages trouvé"
        
        ATTENTION_TOLLS_PRESENT = "Attention: l'itinéraire sans péage contient quand même {count} péages"
        
        # Coordinate validation errors
        COORDINATE_VALIDATION_ERROR = "Erreur de validation des coordonnées: {error}"
        INVALID_COORDINATE_FORMAT = "Format de coordonnée invalide: attendu [longitude, latitude]"
        COORDINATE_OUT_OF_BOUNDS = "Coordonnée hors limites géographiques"
        
    @staticmethod
    def get_barriers_csv_path():
        """
        Retourne le chemin complet vers le fichier barriers.csv.
        Peut être étendu pour gérer différents environnements.
        """
        return TollOptimizationConfig.BARRIERS_CSV_PATH