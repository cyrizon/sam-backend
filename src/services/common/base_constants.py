"""
base_constants.py
----------------

Constantes de base communes aux modules toll et budget.
Responsabilité unique : centraliser les constantes partagées.
"""

class BaseOptimizationConfig:
    """Configuration de base pour l'optimisation de routes."""
    
    # === Distance and proximity limits ===
    MAX_DISTANCE_SEARCH_M = 100000  # 100 km - Distance maximale pour chercher des péages
    MAX_NEARBY_TOLLS_TO_TEST = 10   # Nombre maximum de péages proches à tester
    
    # === Performance and progress thresholds ===
    COMBINATION_PROGRESS_INTERVAL = 10  # Affichage du progrès toutes les N combinaisons
    
    # === File paths ===
    BARRIERS_CSV_PATH = "data/barriers.csv"  # Chemin vers les données de péages
    
    # === Route calculation defaults ===
    DEFAULT_MAX_COMB_SIZE = 2  # Taille max par défaut des combinaisons
    DEFAULT_VEH_CLASS = "c1"   # Classe de véhicule par défaut
    
    # === Common Status codes ===
    class StatusCodes:
        """Status codes standardisés pour les résultats."""
        
        # Success codes        
        SUCCESS = "SUCCESS"
        NO_TOLL_SUCCESS = "NO_TOLL_SUCCESS"
        ONE_OPEN_TOLL_SUCCESS = "ONE_OPEN_TOLL_SUCCESS"
        MULTI_TOLL_SUCCESS = "MULTI_TOLL_SUCCESS"
        GENERAL_STRATEGY = "GENERAL_STRATEGY"
        GENERAL_STRATEGY_WITH_MIN_TOLLS = "GENERAL_STRATEGY_WITH_MIN_TOLLS"
        MINIMUM_TOLLS_SOLUTION = "MINIMUM_TOLLS_SOLUTION"
        
        # Constraint-based codes (new simplified approach)
        CONSTRAINT_RESPECTED = "CONSTRAINT_RESPECTED"
        CONSTRAINT_EXCEEDED_BY_ONE = "CONSTRAINT_EXCEEDED_BY_ONE"
        
        # Warning codes
        SOME_TOLLS_PRESENT = "SOME_TOLLS_PRESENT"
        
        # Error codes
        NO_TOLL_ROUTE_NOT_POSSIBLE = "NO_TOLL_ROUTE_NOT_POSSIBLE"
        NO_OPEN_TOLL_FOUND = "NO_OPEN_TOLL_FOUND"
        NO_VALID_OPEN_TOLL_ROUTE = "NO_VALID_OPEN_TOLL_ROUTE"
        NO_VALID_ROUTE_WITH_MAX_TOLLS = "NO_VALID_ROUTE_WITH_MAX_TOLLS"
        NO_VALID_ROUTE_WITH_MAX_ONE_TOLL = "NO_VALID_ROUTE_WITH_MAX_ONE_TOLL"
        ORS_CONNECTION_ERROR = "ORS_CONNECTION_ERROR"
        CRITICAL_ERROR = "CRITICAL_ERROR"
        INVALID_MAX_PRICE = "INVALID_MAX_PRICE"
        INVALID_MAX_PRICE_PERCENT = "INVALID_MAX_PRICE_PERCENT"
        
        # Budget-specific codes
        BUDGET_ZERO_NO_TOLL_SUCCESS = "BUDGET_ZERO_NO_TOLL_SUCCESS"
        BUDGET_ALREADY_SATISFIED = "BUDGET_ALREADY_SATISFIED"
        BUDGET_SATISFIED = "BUDGET_SATISFIED"
        FREE_ALTERNATIVE_FOUND = "FREE_ALTERNATIVE_FOUND"
        FASTEST_AMONG_CHEAPEST_FOUND = "FASTEST_AMONG_CHEAPEST_FOUND"
        CLOSEST_TO_BUDGET_FOUND = "CLOSEST_TO_BUDGET_FOUND"
        EXPANDED_BUDGET_SATISFIED = "EXPANDED_BUDGET_SATISFIED"
        BUDGET_ZERO_SOME_TOLLS_PRESENT = "BUDGET_ZERO_SOME_TOLLS_PRESENT"        
        ONLY_CHEAPEST_FOUND = "ONLY_CHEAPEST_FOUND"
        NO_ROUTE_WITHIN_BUDGET = "NO_ROUTE_WITHIN_BUDGET"
        NO_ROUTE_WITHIN_BUDGET_RETURNING_FASTEST_AMONG_CHEAPEST = "NO_ROUTE_WITHIN_BUDGET_RETURNING_FASTEST_AMONG_CHEAPEST"
        NO_TOLLS_FOUND = "NO_TOLLS_FOUND"
        NO_ALTERNATIVE_FOUND = "NO_ALTERNATIVE_FOUND"
        NO_TOLL_ALTERNATIVE_FOUND = "NO_TOLL_ALTERNATIVE_FOUND"
        FALLBACK_BASE_ROUTE_USED = "FALLBACK_BASE_ROUTE_USED"
        LIMITED_ALTERNATIVES_FOUND = "LIMITED_ALTERNATIVES_FOUND"
        ONLY_BASE_ROUTE_AVAILABLE = "ONLY_BASE_ROUTE_AVAILABLE"
        PERCENTAGE_BUDGET_IMPOSSIBLE = "PERCENTAGE_BUDGET_IMPOSSIBLE"
    
    # === Common Messages ===
    class Messages:
        """Messages standardisés pour les logs."""
        
        # Progress messages
        PROGRESS_COMBINATIONS = "Progression: {count} combinaisons testées"
        
        # Route messages
        ROUTE_ALTERNATIVE = "Route alternative: coût={cost}€, durée={duration:.1f}min"
        ROUTE_GRATUITE_TROUVEE = "Route gratuite trouvée !"
        
        # Toll messages
        TOLLS_ON_ROUTE = "Péages sur la route :"
        TOLLS_NEARBY = "Péages proches :"
        ATTENTION_TOLLS_PRESENT = "Attention: l'itinéraire sans péage contient quand même {count} péages"
        
        # Results logging
        RESULT_BASE = "[RESULT] Base: {toll_count} péages, coût={cost}€, durée={duration:.1f} min"
        RESULT_CHEAPEST = "[RESULT] Cheapest: {toll_count} péages, coût={cost}€, durée={duration:.1f} min"
        RESULT_FASTEST = "[RESULT] Fastest: {toll_count} péages, coût={cost}€, durée={duration:.1f} min"
        RESULT_MIN_TOLLS = "[RESULT] Minimum tolls: {toll_count} péages, coût={cost}€, durée={duration:.1f} min"
        
        # Validation errors
        COORDINATE_VALIDATION_ERROR = "Erreur de validation des coordonnées: {error}"
        INVALID_COORDINATE_FORMAT = "Format de coordonnée invalide: attendu [longitude, latitude]"
        COORDINATE_OUT_OF_BOUNDS = "Coordonnée hors limites géographiques"
        
        # Common error messages
        VALIDATION_FAILED = "Échec de la validation des paramètres"
        STRATEGY_FAILED = "Échec de la stratégie principale, activation du fallback"
        CRITICAL_ERROR_OCCURRED = "Erreur critique détectée: {error}"
    
    @staticmethod
    def get_barriers_csv_path():
        """Retourne le chemin vers le fichier des barrières."""
        return BaseOptimizationConfig.BARRIERS_CSV_PATH
