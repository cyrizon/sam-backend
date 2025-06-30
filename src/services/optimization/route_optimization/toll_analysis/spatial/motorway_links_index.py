"""
Motorway Links Spatial Index
===========================

Index spatial pour les entrées et sorties d'autoroute.
Utilise CompleteMotorwayLink du cache V2 pour une détection optimisée.
"""

import rtree.index
from typing import List, Dict, Tuple, Optional
from ...utils.cache_accessor import CacheAccessor
from src.cache.models.complete_motorway_link import CompleteMotorwayLink


class MotorwayLinksSpatialIndex:
    """Index spatial R-tree pour les entrées et sorties d'autoroute."""
    
    def __init__(self, link_type: str = "ENTRY"):
        """
        Initialise l'index spatial pour un type de lien.
        
        Args:
            link_type: "ENTRY" pour entrées, "EXIT" pour sorties
        """
        self.link_type = link_type
        self.index = None
        self.links_dict = {}  # int_id -> CompleteMotorwayLink
        self.id_mapping = {}  # string_id -> int_id  
        self.reverse_id_mapping = {}  # int_id -> string_id
        self._build_index()
    
    def _build_index(self) -> None:
        """Construit l'index spatial R-tree à partir du cache V2."""
        print(f"🗂️ Construction de l'index spatial pour {self.link_type}...")
        
        # Récupérer les liens selon le type
        if self.link_type == "ENTRY":
            links = CacheAccessor.get_entry_links()
        elif self.link_type == "EXIT":
            links = CacheAccessor.get_exit_links()
        else:
            links = CacheAccessor.get_complete_motorway_links()
        
        if not links:
            print(f"⚠️ Aucun lien {self.link_type} trouvé dans le cache V2")
            self.index = rtree.index.Index()
            return
        
        # Construire l'index R-tree
        self.index = rtree.index.Index()
        
        int_id = 0  # Compteur pour les IDs entiers
        
        for link in links:
            # Utiliser les coordonnées de début pour les entrées, fin pour les sorties
            if self.link_type == "ENTRY":
                coordinates = link.get_start_point()
            else:  # EXIT
                coordinates = link.get_end_point()
            
            if not coordinates or len(coordinates) < 2:
                continue
            
            lon, lat = coordinates[0], coordinates[1]
            
            # Bounding box ponctuelle
            bbox = (lon, lat, lon, lat)
            
            # Mapper string ID vers int ID
            string_id = link.link_id
            self.id_mapping[string_id] = int_id
            self.reverse_id_mapping[int_id] = string_id
            
            # Insérer dans l'index avec ID entier
            self.index.insert(int_id, bbox)
            
            # Garder référence du lien avec ID entier
            self.links_dict[int_id] = link
            
            int_id += 1
        
        print(f"✅ Index spatial {self.link_type} construit : {len(self.links_dict)} liens indexés")
    
    def query_nearby_links(
        self, 
        coordinates: List[float], 
        buffer_km: float = 0.2
    ) -> List[CompleteMotorwayLink]:
        """
        Trouve les liens proches d'un point donné.
        
        Args:
            coordinates: [lon, lat] du point de référence
            buffer_km: Distance de recherche en km (défaut: 200m)
            
        Returns:
            Liste des liens proches
        """
        if not self.index or not coordinates or len(coordinates) < 2:
            return []
        
        lon, lat = coordinates[0], coordinates[1]
        
        # Conversion approximative km -> degrés
        # 1 km ≈ 0.009 degrés (approximation)
        margin = buffer_km * 0.009
        
        # Bounding box élargie
        bbox = (
            lon - margin,
            lat - margin,
            lon + margin,
            lat + margin
        )
        
        # Requête R-tree
        candidate_ids = list(self.index.intersection(bbox))
        
        # Retourner les objets liens
        nearby_links = [
            self.links_dict[link_id] 
            for link_id in candidate_ids 
            if link_id in self.links_dict
        ]
        
        print(f"   🎯 Liens {self.link_type} proches : {len(nearby_links)} trouvés "
              f"(buffer: {buffer_km}km)")
        
        return nearby_links
    
    def query_links_along_route(
        self, 
        route_coordinates: List[List[float]], 
        buffer_km: float = 0.2
    ) -> List[CompleteMotorwayLink]:
        """
        Trouve les liens le long d'une route.
        
        Args:
            route_coordinates: Coordonnées de la route
            buffer_km: Distance de recherche en km
            
        Returns:
            Liste des liens le long de la route
        """
        if not self.index or not route_coordinates:
            return []
        
        # Calculer la bounding box de la route
        lons = [coord[0] for coord in route_coordinates]
        lats = [coord[1] for coord in route_coordinates]
        
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        
        # Élargir la bbox
        margin = buffer_km * 0.009
        
        expanded_bbox = (
            min_lon - margin,
            min_lat - margin, 
            max_lon + margin,
            max_lat + margin
        )
        
        # Requête R-tree
        candidate_ids = list(self.index.intersection(expanded_bbox))
        
        # Retourner les objets liens
        route_links = [
            self.links_dict[link_id] 
            for link_id in candidate_ids 
            if link_id in self.links_dict
        ]
        
        print(f"   🛣️ Liens {self.link_type} le long de la route : {len(route_links)} trouvés")
        
        return route_links
    
    def get_links_with_tolls(self) -> List[CompleteMotorwayLink]:
        """
        Retourne uniquement les liens qui ont des péages associés.
        
        Returns:
            Liste des liens avec péages
        """
        return [
            link for link in self.links_dict.values() 
            if link.has_toll()
        ]
    
    def get_index_stats(self) -> Dict:
        """
        Retourne les statistiques de l'index spatial.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        links_with_tolls = self.get_links_with_tolls()
        
        return {
            'link_type': self.link_type,
            'total_links': len(self.links_dict),
            'index_available': self.index is not None,
            'links_with_tolls': len(links_with_tolls),
            'operators': len(set(
                link.associated_toll.operator 
                for link in links_with_tolls 
                if link.associated_toll and link.associated_toll.operator
            ))
        }
    
    def rebuild_index(self) -> bool:
        """
        Reconstruit l'index spatial.
        
        Returns:
            True si reconstruction réussie
        """
        try:
            self._build_index()
            return True
        except Exception as e:
            print(f"❌ Erreur reconstruction index {self.link_type} : {e}")
            return False
