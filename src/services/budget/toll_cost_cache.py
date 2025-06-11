"""
toll_cost_cache.py
-----------------

Cache simple et efficace pour les coûts de péages par classe de véhicule.
Responsabilité unique : éviter les recalculs de coûts identiques.
"""

from typing import Dict, Optional, Tuple
from threading import Lock
import hashlib


class TollCostCache:
    """
    Cache thread-safe pour les coûts de péages.
    Clé : (toll_id, veh_class) -> Valeur : cost
    """
    
    def __init__(self):
        """Initialise le cache avec verrou pour thread-safety."""
        self._cache: Dict[str, float] = {}
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
    
    def _generate_key(self, toll_id: str, veh_class: str) -> str:
        """
        Génère une clé unique pour le cache.
        
        Args:
            toll_id: Identifiant du péage
            veh_class: Classe de véhicule (c1, c2, etc.)
            
        Returns:
            str: Clé unique pour le cache
        """
        return f"{toll_id}:{veh_class}"
    
    def get(self, toll_id: str, veh_class: str) -> Optional[float]:
        """
        Récupère le coût depuis le cache.
        
        Args:
            toll_id: Identifiant du péage
            veh_class: Classe de véhicule
            
        Returns:
            float: Coût en cache ou None si absent
        """
        key = self._generate_key(toll_id, veh_class)
        
        with self._lock:
            if key in self._cache:
                self._hits += 1
                return self._cache[key]
            else:
                self._misses += 1
                return None
    
    def put(self, toll_id: str, veh_class: str, cost: float) -> None:
        """
        Stocke un coût dans le cache.
        
        Args:
            toll_id: Identifiant du péage
            veh_class: Classe de véhicule
            cost: Coût à mettre en cache
        """
        key = self._generate_key(toll_id, veh_class)
        
        with self._lock:
            self._cache[key] = cost
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Retourne les statistiques du cache.
        
        Returns:
            dict: Statistiques (hits, misses, size, hit_rate)
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._cache),
                "hit_rate": round(hit_rate, 2)
            }
    
    def clear(self) -> None:
        """Vide le cache et remet les statistiques à zéro."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def log_statistics(self) -> None:
        """Affiche les statistiques du cache."""
        stats = self.get_statistics()
        print(f"📊 Cache péages: {stats['hits']} hits, {stats['misses']} misses, "
              f"{stats['hit_rate']}% hit rate, {stats['size']} entrées")


# Instance globale du cache (singleton simple)
toll_cost_cache = TollCostCache()
