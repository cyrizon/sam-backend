"""
smart_toll_cache.py
------------------

Cache intelligent pour les coûts de péages respectant la logique des péages fermés.
Responsabilité unique : optimiser les calculs tout en respectant les séquences de péages.
"""

from typing import List, Dict, Optional, Tuple
from threading import Lock
import hashlib
import time
from src.services.toll_cost import add_marginal_cost
from src.utils.route_utils import is_toll_open_system


class SmartTollCache:
    """
    Cache intelligent qui comprend la logique des péages fermés.
    Cache les séquences complètes de péages avec leurs coûts réels.
    """
    
    def __init__(self, max_size: int = 500, ttl_seconds: int = 3600):
        """
        Initialise le cache intelligent.
        
        Args:
            max_size: Nombre maximum de séquences en cache
            ttl_seconds: Durée de vie des entrées (1h par défaut)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict] = {}
        self._access_times: Dict[str, float] = {}
        self._creation_times: Dict[str, float] = {}
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
    
    def _generate_sequence_key(self, tolls_sequence: List[Dict], veh_class: str) -> str:
        """
        Génère une clé unique pour une séquence de péages.
        
        Args:
            tolls_sequence: Séquence ordonnée de péages
            veh_class: Classe de véhicule
            
        Returns:
            str: Clé de cache unique
        """
        # Créer une signature basée sur l'ordre et les IDs des péages
        toll_ids = [toll.get("id", "unknown") for toll in tolls_sequence]
        content = f"{toll_ids}_{veh_class}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_sequence_cost(self, tolls_sequence: List[Dict], veh_class: str) -> Optional[List[Dict]]:
        """
        Récupère une séquence de péages avec coûts depuis le cache.
        
        Args:
            tolls_sequence: Séquence de péages à vérifier
            veh_class: Classe de véhicule
            
        Returns:
            List[Dict] | None: Séquence avec coûts si en cache, None sinon
        """
        if not tolls_sequence:
            return []
        
        key = self._generate_sequence_key(tolls_sequence, veh_class)
        current_time = time.time()
        
        with self._lock:
            if key in self._cache:
                # Vérifier la fraîcheur
                if current_time - self._creation_times[key] > self.ttl_seconds:
                    self._remove_entry(key)
                    self._misses += 1
                    return None
                
                # Mettre à jour le temps d'accès pour LRU
                self._access_times[key] = current_time
                self._hits += 1
                
                # Retourner une copie des données mises en cache
                cached_sequence = self._cache[key]["tolls_with_costs"]
                return [toll.copy() for toll in cached_sequence]
            
            self._misses += 1
            return None
    
    def put_sequence_cost(self, tolls_sequence: List[Dict], veh_class: str, total_cost: float) -> None:
        """
        Stocke une séquence de péages avec coûts dans le cache.
        
        Args:
            tolls_sequence: Séquence de péages avec coûts calculés
            veh_class: Classe de véhicule  
            total_cost: Coût total de la séquence
        """
        if not tolls_sequence:
            return
        
        key = self._generate_sequence_key(tolls_sequence, veh_class)
        current_time = time.time()
        
        with self._lock:
            # Éviction si cache plein
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_oldest()
            
            # Stocker une copie de la séquence
            self._cache[key] = {
                "tolls_with_costs": [toll.copy() for toll in tolls_sequence],
                "total_cost": total_cost,
                "veh_class": veh_class
            }
            self._access_times[key] = current_time
            self._creation_times[key] = current_time
    
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
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
            self._creation_times.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> Dict:
        """
        Retourne les statistiques du cache.
        
        Returns:
            dict: Statistiques d'utilisation du cache
        """
        with self._lock:
            current_time = time.time()
            valid_entries = sum(
                1 for key in self._cache.keys()
                if current_time - self._creation_times[key] <= self.ttl_seconds
            )
            
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "total_entries": len(self._cache),
                "valid_entries": valid_entries,
                "max_size": self.max_size,
                "usage_ratio": valid_entries / self.max_size if self.max_size > 0 else 0,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 2)
            }


# Instance globale du cache intelligent
_smart_toll_cache = SmartTollCache()


def add_marginal_cost_smart_cached(tolls: List[Dict], veh_class: str = "c1") -> None:
    """
    Version intelligente avec cache de add_marginal_cost.
    Respecte la logique des péages fermés et cache les séquences complètes.
    
    Args:
        tolls: Liste des péages à enrichir avec les coûts
        veh_class: Classe de véhicule pour le calcul des coûts
    """
    if not tolls:
        return
    
    # Vérifier le cache pour la séquence complète
    cached_sequence = _smart_toll_cache.get_sequence_cost(tolls, veh_class)
    if cached_sequence is not None:
        # Appliquer les coûts depuis le cache
        for i, toll in enumerate(tolls):
            if i < len(cached_sequence):
                toll.update(cached_sequence[i])
        
        total_cost = sum(t.get("cost", 0) for t in tolls)
        print(f"🎯 Cache intelligent: séquence complète en cache, coût total: {total_cost:.2f}€")
        return
    
    # Calcul normal si pas en cache
    add_marginal_cost(tolls, veh_class)
    
    # Mettre en cache la séquence complète
    total_cost = sum(t.get("cost", 0) for t in tolls)
    _smart_toll_cache.put_sequence_cost(tolls, veh_class, total_cost)
    
    print(f"🔥 Cache intelligent: calcul et mise en cache nouvelle séquence, coût total: {total_cost:.2f}€")


def get_smart_cache_stats() -> Dict:
    """
    Retourne les statistiques du cache intelligent.
    
    Returns:
        dict: Statistiques d'utilisation du cache
    """
    return _smart_toll_cache.get_stats()


def clear_smart_toll_cache() -> None:
    """Vide le cache intelligent."""
    _smart_toll_cache.clear()
    print("🗑️ Cache intelligent des péages vidé")


def log_smart_cache_stats() -> None:
    """Affiche les statistiques du cache intelligent."""
    stats = get_smart_cache_stats()
    print(f"📊 Cache intelligent: {stats['hits']} hits, {stats['misses']} misses, "
          f"{stats['hit_rate']}% hit rate, {stats['valid_entries']} séquences")
