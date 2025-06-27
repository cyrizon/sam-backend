"""
Spatial Index Manager
====================

Gère l'indexation spatiale R-tree pour une détection optimisée des péages.
Responsabilité unique : index spatial et requêtes géographiques rapides.
"""

import rtree.index
from typing import List, Dict, Tuple, Optional
from ...utils.cache_accessor import CacheAccessor


class SpatialIndexManager:
    """Gestionnaire d'index spatial R-tree optimisé."""
    
    def __init__(self):
        """Initialise le gestionnaire d'index spatial."""
        self.index = None
        self.tolls_dict = {}
        self._build_index()
    
    def _build_index(self) -> None:
        """Construit l'index spatial R-tree à partir du cache."""
        print("🗂️ Construction de l'index spatial R-tree...")
        
        # Récupérer les péages matchés du cache
        matched_tolls = CacheAccessor.get_matched_tolls()
        
        if not matched_tolls:
            print("⚠️ Aucun péage trouvé dans le cache")
            self.index = rtree.index.Index()
            return
        
        # Construire l'index R-tree
        self.index = rtree.index.Index()
        
        for toll in matched_tolls:
            if not toll.osm_coordinates or len(toll.osm_coordinates) < 2:
                continue
            
            lon, lat = toll.osm_coordinates[0], toll.osm_coordinates[1]
            
            # Bounding box ponctuelle (point = rectangle de taille 0)
            bbox = (lon, lat, lon, lat)
            
            # Insérer dans l'index
            self.index.insert(toll.osm_id, bbox)
            
            # Garder référence du péage
            self.tolls_dict[toll.osm_id] = toll
        
        print(f"✅ Index spatial construit : {len(self.tolls_dict)} péages indexés")
    
    def query_bbox_candidates(self, route_coordinates: List[List[float]]) -> List:
        """
        Requête spatiale pour les péages candidats dans la bounding box élargie.
        
        Args:
            route_coordinates: Coordonnées de la route
            
        Returns:
            Liste des péages candidats
        """
        if not self.index or not route_coordinates:
            return []
        
        # Calculer la bounding box de la route
        lons = [coord[0] for coord in route_coordinates]
        lats = [coord[1] for coord in route_coordinates]
        
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        
        # Élargir la bbox pour inclure péages "autour" (<1km)
        # ~1km = ~0.01 degrés (approximation)
        margin = 0.015  # 1.5km pour être sûr
        
        expanded_bbox = (
            min_lon - margin,
            min_lat - margin, 
            max_lon + margin,
            max_lat + margin
        )
        
        # Requête R-tree (ultra-rapide)
        candidate_ids = list(self.index.intersection(expanded_bbox))
        
        # Retourner les objets péages
        candidates = [
            self.tolls_dict[toll_id] 
            for toll_id in candidate_ids 
            if toll_id in self.tolls_dict
        ]
        
        print(f"   🎯 Pré-filtrage spatial : {len(candidates)} candidats "
              f"(sur {len(self.tolls_dict)} péages totaux)")
        
        return candidates
    
    def get_index_stats(self) -> Dict:
        """
        Retourne les statistiques de l'index spatial.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        return {
            'total_tolls': len(self.tolls_dict),
            'index_available': self.index is not None,
            'matched_tolls': sum(1 for t in self.tolls_dict.values() if t.csv_id),
            'open_system_tolls': sum(1 for t in self.tolls_dict.values() if t.csv_role == 'O'),
            'closed_system_tolls': sum(1 for t in self.tolls_dict.values() if t.csv_role == 'F')
        }
    
    def rebuild_index(self) -> bool:
        """
        Reconstruit l'index spatial (en cas de mise à jour du cache).
        
        Returns:
            True si reconstruction réussie
        """
        try:
            self._build_index()
            return True
        except Exception as e:
            print(f"❌ Erreur reconstruction index : {e}")
            return False
