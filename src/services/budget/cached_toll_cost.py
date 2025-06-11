"""
cached_toll_cost.py
------------------

Adaptateur pour intégrer le cache dans les calculs de coûts de péages existants.
Responsabilité unique : optimiser les appels à add_marginal_cost avec cache.
"""

from typing import List, Dict
from src.services.toll_cost import add_marginal_cost
from src.services.budget.toll_cost_cache import toll_cost_cache


def add_marginal_cost_cached(tolls: List[Dict], veh_class: str = "c1") -> None:
    """
    Version optimisée avec cache de add_marginal_cost.
    
    Args:
        tolls: Liste des péages à enrichir avec les coûts
        veh_class: Classe de véhicule pour le calcul des coûts
    """
    if not tolls:
        return
    
    # Séparer les péages avec coût en cache vs à calculer
    tolls_to_calculate = []
    cached_count = 0
    
    for toll in tolls:
        toll_id = toll.get("id") or toll.get("name", "unknown")
        
        # Vérifier le cache
        cached_cost = toll_cost_cache.get(toll_id, veh_class)
        
        if cached_cost is not None:
            # Utiliser le coût en cache
            toll["cost"] = cached_cost
            cached_count += 1
        else:
            # Marquer pour calcul
            tolls_to_calculate.append(toll)
    
    # Calculer les coûts manquants
    if tolls_to_calculate:
        add_marginal_cost(tolls_to_calculate, veh_class)
        
        # Mettre en cache les nouveaux coûts
        for toll in tolls_to_calculate:
            toll_id = toll.get("id") or toll.get("name", "unknown")
            cost = toll.get("cost", 0)
            toll_cost_cache.put(toll_id, veh_class, cost)
    
    # Logging des performances du cache
    if cached_count > 0 or tolls_to_calculate:
        total_tolls = len(tolls)
        calculated_count = len(tolls_to_calculate)
        total_cost = sum(t.get("cost", 0) for t in tolls)
        
        print(f"🎯 Cache péages: {cached_count}/{total_tolls} en cache, "
              f"{calculated_count} calculés, coût total: {total_cost:.2f}€")


def get_toll_cost_cached(toll: Dict, veh_class: str = "c1") -> float:
    """
    Récupère le coût d'un péage unique avec cache.
    
    Args:
        toll: Données du péage
        veh_class: Classe de véhicule
        
    Returns:
        float: Coût du péage
    """
    toll_id = toll.get("id") or toll.get("name", "unknown")
    
    # Vérifier le cache
    cached_cost = toll_cost_cache.get(toll_id, veh_class)
    
    if cached_cost is not None:
        return cached_cost
    
    # Calculer et mettre en cache
    tolls_copy = [toll.copy()]
    add_marginal_cost(tolls_copy, veh_class)
    
    cost = tolls_copy[0].get("cost", 0)
    toll_cost_cache.put(toll_id, veh_class, cost)
    
    return cost


def clear_toll_cost_cache() -> None:
    """Vide le cache des coûts de péages."""
    toll_cost_cache.clear()
    print("🗑️ Cache des coûts de péages vidé")


def log_toll_cost_cache_stats() -> None:
    """Affiche les statistiques du cache."""
    toll_cost_cache.log_statistics()
