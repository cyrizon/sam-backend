"""
toll_cost.py
------------

Calcule le *surcoût marginal* (classe véhicule c1…c5) apporté par
chaque péage de la séquence retournée par `locate_tolls`.

Hypothèse : on paie
  • les gares 'O' à coût fixe (ligne entree_id==sortie_id dans virtual_edges)
  • les gares 'S' (sortie) – tarif (entrée précédente ➜ cette sortie)
Les gares 'E' ne déclenchent pas de paiement.

On retourne la séquence assortie du champ `cost`, puis un tri décroissant.
"""
from __future__ import annotations
from typing import List, Dict
import os

import pandas as pd

def _load_edges():
    """Load virtual edges data with toll costs"""
    file_path = os.path.join(os.path.dirname(__file__), '../../data/virtual_edges.csv')
    df = pd.read_csv(file_path)
    price_cols = ['c1', 'c2', 'c3', 'c4', 'c5']
    return df.set_index(["entree", "sortie"])[price_cols]

_EDGES = _load_edges()

def add_marginal_cost(
    tolls: List[Dict],
    veh_class: str = "c1",
) -> List[Dict]:
    """
    Ajoute le champ `cost` à chaque dict selon le format virtual_edges.
    - Si id commence par APRR_O : péage ouvert, coût = (id, id)
    - Si id commence par APRR_F : péage fermé, coût à la sortie (entrée précédente ➜ sortie)
    """
    prev_entry = None
    for t in tolls:
        rid = t["id"]
        cost = 0.0
        # Rôle déduit de l'id
        print(f"Calcul du coût pour le péage {rid} ({veh_class})")
        if rid.startswith("APRR_O"):
            # Péage ouvert : coût fixe (entrée = sortie)
            try:
                cost = _EDGES.loc[(rid, rid)][veh_class]
                print(f"Coût fixe pour {rid} : {cost}")
            except KeyError:
                cost = 0.0
            prev_entry = None  # On repart de zéro
        elif rid.startswith("APRR_F"):
            # Péage fermé : on paie à la sortie, donc si on a une entrée précédente
            if prev_entry is not None:
                try:
                    cost = _EDGES.loc[(prev_entry, rid)][veh_class]
                    print(f"Coût pour {prev_entry} ➜ {rid} : {cost}")
                except KeyError:
                    cost = 0.0
                prev_entry = None
            else:
                # On mémorise l'entrée
                prev_entry = rid
        else:
            # Cas inattendu
            cost = 0.0
        t["cost"] = float(cost)
    return tolls

def rank_by_saving(
    tolls: List[Dict],
    max_keep: int,
) -> List[Dict]:
    """
    Renvoie la *liste des péages à éviter* pour respecter max_keep,
    triée par coût décroissant (ceux-là rapportent le plus à éviter).
    """
    excess = max(0, len(tolls) - max_keep)
    if excess == 0:
        return []
    sorted_tolls = sorted(
        [t for t in tolls if t["cost"] > 0], key=lambda d: d["cost"], reverse=True
    )
    return sorted_tolls[:excess]

# === CACHE INTELLIGENT POUR OPTIMISATION PHASE 1 ===

from typing import Dict, Tuple, Optional
import hashlib
import time

class TollCostCache:
    """
    Cache intelligent pour les calculs de coûts de péages avec éviction basée sur l'usage.
    Optimise les performances en évitant les recalculs coûteux.
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        Initialise le cache avec une taille et durée de vie configurables.
        
        Args:
            max_size: Nombre maximum d'entrées en cache
            ttl_seconds: Durée de vie des entrées en secondes (1h par défaut)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict] = {}
        self._access_times: Dict[str, float] = {}
        self._creation_times: Dict[str, float] = {}
    
    def _generate_key(self, tolls_ids: Tuple[str, ...], veh_class: str) -> str:
        """
        Génère une clé unique pour la combinaison péages + classe véhicule.
        
        Args:
            tolls_ids: Tuple ordonné des IDs de péages
            veh_class: Classe de véhicule (c1, c2, etc.)
            
        Returns:
            str: Clé de cache unique
        """
        # Créer une signature basée sur les IDs triés et la classe véhicule
        content = f"{sorted(tolls_ids)}_{veh_class}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, tolls_ids: Tuple[str, ...], veh_class: str) -> Optional[float]:
        """
        Récupère le coût total en cache pour une combinaison donnée.
        
        Args:
            tolls_ids: Tuple des IDs de péages
            veh_class: Classe de véhicule
            
        Returns:
            float | None: Coût total si trouvé en cache, None sinon
        """
        key = self._generate_key(tolls_ids, veh_class)
        current_time = time.time()
        
        if key in self._cache:
            # Vérifier la fraîcheur
            if current_time - self._creation_times[key] > self.ttl_seconds:
                self._remove_entry(key)
                return None
            
            # Mettre à jour le temps d'accès pour LRU
            self._access_times[key] = current_time
            return self._cache[key]["total_cost"]
        
        return None
    
    def put(self, tolls_ids: Tuple[str, ...], veh_class: str, total_cost: float) -> None:
        """
        Stocke un coût total en cache.
        
        Args:
            tolls_ids: Tuple des IDs de péages
            veh_class: Classe de véhicule  
            total_cost: Coût total à stocker
        """
        key = self._generate_key(tolls_ids, veh_class)
        current_time = time.time()
        
        # Éviction si cache plein
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_oldest()
        
        self._cache[key] = {
            "total_cost": total_cost,
            "tolls_ids": tolls_ids,
            "veh_class": veh_class
        }
        self._access_times[key] = current_time
        self._creation_times[key] = current_time
    
    def get_combination_cost(self, tolls_list: List[Dict], veh_class: str) -> Optional[float]:
        """
        Récupère le coût pour une liste de péages avec leurs détails.
        
        Args:
            tolls_list: Liste des dictionnaires de péages
            veh_class: Classe de véhicule
            
        Returns:
            float | None: Coût total si trouvé, None sinon
        """
        tolls_ids = tuple(toll["id"] for toll in tolls_list)
        return self.get(tolls_ids, veh_class)
    
    def put_combination_cost(self, tolls_list: List[Dict], veh_class: str, total_cost: float) -> None:
        """
        Stocke le coût pour une liste de péages avec leurs détails.
        
        Args:
            tolls_list: Liste des dictionnaires de péages
            veh_class: Classe de véhicule
            total_cost: Coût total à stocker
        """
        tolls_ids = tuple(toll["id"] for toll in tolls_list)
        self.put(tolls_ids, veh_class, total_cost)
    
    def _evict_oldest(self) -> None:
        """Éviction LRU : supprime l'entrée la moins récemment utilisée."""
        if not self._cache:
            return
        
        oldest_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        self._remove_entry(oldest_key)
    
    def _remove_entry(self, key: str) -> None:
        """Supprime une entrée du cache."""
        self._cache.pop(key, None)
        self._access_times.pop(key, None)
        self._creation_times.pop(key, None)
    
    def clear(self) -> None:
        """Vide complètement le cache."""
        self._cache.clear()
        self._access_times.clear()
        self._creation_times.clear()
    
    def get_stats(self) -> Dict:
        """
        Retourne les statistiques du cache.
        
        Returns:
            dict: Statistiques d'utilisation du cache
        """
        current_time = time.time()
        valid_entries = sum(
            1 for key in self._cache.keys()
            if current_time - self._creation_times[key] <= self.ttl_seconds
        )
        
        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "max_size": self.max_size,
            "usage_ratio": valid_entries / self.max_size if self.max_size > 0 else 0
        }

# Instance globale du cache pour utilisation partagée
_toll_cost_cache = TollCostCache()

def add_marginal_cost_cached(
    tolls: List[Dict],
    veh_class: str = "c1",
) -> List[Dict]:
    """
    Version optimisée avec cache de add_marginal_cost.
    
    Args:
        tolls: Liste des péages à traiter
        veh_class: Classe de véhicule pour le calcul des coûts
        
    Returns:
        List[Dict]: Liste des péages avec coûts calculés et mis en cache
    """
    if not tolls:
        return tolls
    
    # Vérifier le cache pour la combinaison complète
    cached_cost = _toll_cost_cache.get_combination_cost(tolls, veh_class)
    if cached_cost is not None:
        # Appliquer les coûts depuis le cache
        total_from_cache = 0
        for i, toll in enumerate(tolls):
            # Estimation basée sur la proportion (simplifiée)
            toll["cost"] = cached_cost / len(tolls) if len(tolls) > 0 else 0.0
            total_from_cache += toll["cost"]
        
        print(f"Cache hit pour {len(tolls)} péages (coût total: {cached_cost})")
        return tolls
    
    # Calcul normal si pas en cache
    tolls_with_cost = add_marginal_cost(tolls, veh_class)
    
    # Mettre en cache le résultat
    total_cost = sum(toll.get("cost", 0) for toll in tolls_with_cost)
    _toll_cost_cache.put_combination_cost(tolls_with_cost, veh_class, total_cost)
    
    print(f"Cache miss - Calcul et mise en cache pour {len(tolls)} péages (coût total: {total_cost})")
    return tolls_with_cost

def get_cache_stats() -> Dict:
    """
    Retourne les statistiques du cache global.
    
    Returns:
        dict: Statistiques d'utilisation du cache
    """
    return _toll_cost_cache.get_stats()

def clear_toll_cost_cache() -> None:
    """Vide le cache des coûts de péages."""
    _toll_cost_cache.clear()
    print("Cache des coûts de péages vidé.")
