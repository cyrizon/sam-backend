"""
common_messages.py
-----------------

Messages communs entre toll et budget.
Responsabilité unique : centraliser les messages partagés.
"""

class CommonMessages:
    """Messages communs à tous les modules d'optimisation."""
    
    # === Validation messages ===
    COORDINATE_VALIDATION_ERROR = "Erreur de validation des coordonnées: {error}"
    INVALID_COORDINATE_FORMAT = "Format de coordonnée invalide: attendu [longitude, latitude]"
    COORDINATE_OUT_OF_BOUNDS = "Coordonnée hors limites géographiques"
    
    # === Operation tracking ===
    OPERATION_START = "🚀 Début: {operation}"
    OPERATION_SUCCESS = "✅ Succès: {operation}"
    OPERATION_FAILURE = "❌ Échec: {operation} - {error}"
    STRATEGY_SELECTION = "🎯 Stratégie sélectionnée: {strategy}"
    FALLBACK_ACTIVATION = "🔄 Fallback activé: {fallback_type}"
    
    # === Route analysis ===
    ROUTE_FOUND = "Route trouvée: coût={cost}€, durée={duration:.1f}min, péages={toll_count}"
    ROUTE_ALTERNATIVE = "Route alternative: coût={cost}€, durée={duration:.1f}min"
    ROUTE_GRATUITE_TROUVEE = "Route gratuite trouvée !"
    
    # === Progress tracking ===
    PROGRESS_COMBINATIONS = "Progression: {count} combinaisons testées"
    PROGRESS_TOLLS_TESTED = "Péages testés: {tested}/{total}"
    
    # === Toll information ===
    TOLLS_ON_ROUTE = "Péages sur la route :"
    TOLLS_NEARBY = "Péages proches :"
    TOLLS_FOUND_COUNT = "Trouvé {count} péages"
    TOLLS_NONE_FOUND = "Aucun péage trouvé"
    
    # === Results logging ===
    RESULT_BASE = "[RESULT] Base: {toll_count} péages, coût={cost}€, durée={duration:.1f} min"
    RESULT_CHEAPEST = "[RESULT] Cheapest: {toll_count} péages, coût={cost}€, durée={duration:.1f} min"
    RESULT_FASTEST = "[RESULT] Fastest: {toll_count} péages, coût={cost}€, durée={duration:.1f} min"
    RESULT_MIN_TOLLS = "[RESULT] Minimum tolls: {toll_count} péages, coût={cost}€, durée={duration:.1f} min"
    
    # === Error handling ===
    VALIDATION_FAILED = "Échec de la validation des paramètres"
    STRATEGY_FAILED = "Échec de la stratégie principale, activation du fallback"
    CRITICAL_ERROR_OCCURRED = "Erreur critique détectée: {error}"
    ORS_API_ERROR = "Erreur API ORS: {error}"
    
    # === Cost and budget ===
    COST_CALCULATION = "Calcul du coût: {description}"
    COST_TOTAL = "Coût total calculé: {cost}€"
    BUDGET_CONSTRAINT = "Contrainte budgétaire: {constraint}"
    BUDGET_SATISFIED = "✅ Contrainte budgétaire respectée"
    BUDGET_EXCEEDED = "❌ Contrainte budgétaire dépassée"
    
    # === Additional common messages ===
    COMPUTATION_ERROR = "Erreur lors du calcul: {error}"
    NO_TOLLS_FOR_OPTIMIZATION = "Aucun péage trouvé pour l'optimisation."
    TESTING_PROMISING_TOLLS = "Test prioritaire des péages les plus prometteurs..."
    TESTING_INDIVIDUAL_TOLLS = "Test de l'évitement des péages individuels..."
    TESTING_TOLL = "Test prioritaire du péage: {toll_id} (coût: {cost}€)"
    TESTING_TOLL_AVOIDANCE = "Test d'évitement du péage: {toll_id} (coût: {cost}€)"
    FREE_ROUTE_FOUND = "Route gratuite trouvée !"
    TOLLS_NOT_AVOIDED = "⚠️ Certains péages n'ont pas pu être évités: {tolls}"
    NO_ECONOMIC_ROUTE = "Aucune route économique trouvée"
    NO_FAST_ROUTE = "Aucune route rapide trouvée"
    NO_MIN_TOLLS_ROUTE = "Aucune route avec moins de péages trouvée"
    TOLL_NOT_AVOIDED = "Le péage {toll_id} n'a pas pu être évité."
    ROUTE_ALTERNATIVE_INFO = "Route alternative: coût={cost}€, durée={duration:.1f}min"
    TOLL_AVOIDANCE_ERROR = "Erreur lors de l'évitement du péage {toll_id}: {error}"
    
    # === Performance ===
    API_CALL_COUNT = "Appels API effectués: {count}"
    EXECUTION_TIME = "Temps d'exécution: {time:.2f}s"
    OPTIMIZATION_COMPLETE = "Optimisation terminée en {time:.2f}s"
    
    # === Status updates ===
    SEARCHING_ROUTES = "Recherche d'itinéraires en cours..."
    ANALYZING_ROUTES = "Analyse des itinéraires trouvés..."
    OPTIMIZING_ROUTES = "Optimisation des itinéraires..."
    FINALIZING_RESULTS = "Finalisation des résultats..."
