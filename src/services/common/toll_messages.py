"""
toll_messages.py
---------------

Messages spécifiques au module toll.
Responsabilité unique : centraliser les messages de péages.
"""

class TollMessages:
    """Messages spécifiques à l'optimisation de péages."""
    
    # Search messages
    SEARCH_NO_TOLL = "Recherche d'un itinéraire sans péage..."
    SEARCH_ONE_OPEN_TOLL = "Recherche d'un itinéraire avec un seul péage ouvert..."
    SEARCH_MANY_TOLLS = "Recherche d'itinéraires avec max {max_tolls} péages..."
    
    # Toll finding messages
    FOUND_OPEN_TOLLS_NEARBY = "Trouvé {count} péages ouverts à proximité immédiate"
    FOUND_OPEN_TOLLS_NETWORK = "Trouvé {count} péages ouverts dans un rayon de {distance:.1f} km"
    
    NO_OPEN_TOLLS_NEARBY = "Aucune solution trouvée avec les péages ouverts à proximité. Test avec tous les péages ouverts du réseau..."
    NO_OPEN_TOLLS_IN_RADIUS = "Aucun péage à système ouvert trouvé dans un rayon de {distance:.1f} km"
    
    # Solution messages
    SOLUTION_ONE_TOLL = "Solution avec exactement 1 péage: péage={toll_id}, coût={cost}€, durée={duration:.1f}min"
    SOLUTION_MULTIPLE_TOLLS = "Solution avec {toll_count} péages: péage principal={toll_id}, coût={cost}€, durée={duration:.1f}min"
    
    NO_EXACT_ONE_TOLL = "Pas de solution avec exactement un péage ouvert, mais trouvé une solution avec {toll_count} péages"
      # Validation messages
    ROUTE_IGNORED_MAX_TOLLS = "Itinéraire ignoré : {toll_count} péages > max_tolls={max_tolls}"
    AVOIDED_TOLLS_STILL_PRESENT = "Attention : certains péages à éviter sont toujours présents : {present_tolls}"
    IMPOSSIBLE_AVOID_TOLLS = "Impossible d'éviter les péages indésirables sur {part_name}: {unwanted_ids}"
    TARGET_TOLL_MISSING = "Le péage cible {toll_id} n'est pas présent dans l'itinéraire final"
    
    NO_ROUTE_FOUND_MAX_TOLLS = "Aucun itinéraire trouvé respectant la contrainte de max_tolls"
    
    # Debug/Progress messages
    TOLLS_ON_ROUTE = "Péages sur l'itinéraire:"
    TOLLS_NEARBY = "Péages à proximité:"
    PROGRESS_COMBINATIONS = "Combinaisons testées: {count}"
    
    # Error messages
    NO_ECONOMIC_ROUTE = "[RESULT] Pas d'itinéraire économique trouvé respectant la contrainte de max_tolls"
    NO_FAST_ROUTE = "[RESULT] Pas d'itinéraire rapide trouvé respectant la contrainte de max_tolls"
    NO_MIN_TOLLS_ROUTE = "[RESULT] Pas d'itinéraire avec un minimum de péages trouvé"
    
    # Result display messages
    RESULT_BASE = "Route de base: {toll_count} péages, coût={cost}€, durée={duration:.1f}min"
    RESULT_CHEAPEST = "Route la moins chère: {toll_count} péages, coût={cost}€, durée={duration:.1f}min"
    RESULT_FASTEST = "Route la plus rapide: {toll_count} péages, coût={cost}€, durée={duration:.1f}min"
    RESULT_MIN_TOLLS = "Route avec minimum de péages: {toll_count} péages, coût={cost}€, durée={duration:.1f}min"
