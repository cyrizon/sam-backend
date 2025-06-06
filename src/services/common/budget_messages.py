"""
budget_messages.py
-----------------

Messages spécifiques au module budget.
Responsabilité unique : centraliser les messages budgétaires.
"""

class BudgetMessages:
    """Messages spécifiques à l'optimisation budgétaire."""
    
    # Search messages
    SEARCH_ZERO_BUDGET = "Recherche d'un itinéraire avec budget zéro..."
    SEARCH_PERCENTAGE_BUDGET = "Recherche d'un itinéraire avec budget à {percent}% du coût de base..."
    SEARCH_ABSOLUTE_BUDGET = "Recherche d'un itinéraire avec budget maximum de {budget}€..."
    
    # Budget-specific progress messages
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
    
    # Budget results messages
    SOLUTION_PROMETTEUSE = "Solution prometteuse trouvée dans le budget: {cost}€ ≤ {limit}€"
    SOLUTION_WITHIN_BUDGET = "Solution prometteuse trouvée dans le budget: {cost}€ ≤ {budget}€"
    IMPOSSIBLE_NO_TOLL_ROUTE = "Impossible de trouver un itinéraire sans péage: {error}"
    
    # Additional budget-specific messages
    COORDINATES_INFO = "Coordonnées concernées: {coordinates}"
    TOLLS_AVAILABLE = "Péages disponibles pour optimisation: {count}"
    PROMISING_TOLLS = "Péages prometteurs pour combler l'écart: {count}"
    BASE_ROUTE_SUMMARY = "Route de base: {toll_count} péages, {cost}€, {duration:.1f}min"
    BUDGET_STATISTICS = "Budget: {routes_tested} routes testées, {routes_within_budget} dans le budget ({compliance_rate:.1f}%)"
    BEST_CHEAP_ROUTE = "Route la moins chère: {toll_count} péages, {cost}€, {duration:.1f}min {status}"
    BEST_FAST_ROUTE = "Route la plus rapide: {toll_count} péages, {cost}€, {duration:.1f}min {status}"
    BEST_MIN_TOLLS_ROUTE = "Route avec moins de péages: {toll_count} péages, {cost}€, {duration:.1f}min {status}"
    
    # Budget constraint messages
    CONSTRAINT_ZERO_BUDGET = "📊 Contrainte: Budget zéro (routes gratuites uniquement)"
    CONSTRAINT_PERCENTAGE_BUDGET = "📊 Contrainte: {percent}% du coût de base ({base_cost}€) = {actual_limit}€"
    CONSTRAINT_ABSOLUTE_BUDGET = "📊 Contrainte: Budget maximum {budget_limit}€"
    CONSTRAINT_GENERIC = "📊 Contrainte: {budget_type} = {budget_limit}"
    
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
