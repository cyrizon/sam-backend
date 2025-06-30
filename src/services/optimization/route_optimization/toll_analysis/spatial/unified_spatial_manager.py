"""
Unified Spatial Index Manager
============================

Gestionnaire unifié de tous les index spatiaux pour route optimization.
Combine péages, entrées et sorties dans une interface simple.
"""

from typing import List, Dict, Optional
from .spatial_index import SpatialIndexManager  
from .motorway_links_index import MotorwayLinksSpatialIndex
from src.cache.v2.models.toll_booth_station import TollBoothStation
from src.cache.v2.models.complete_motorway_link import CompleteMotorwayLink


class UnifiedSpatialIndexManager:
    """Gestionnaire unifié de tous les index spatiaux."""
    
    def __init__(self):
        """Initialise tous les index spatiaux."""
        print("🚀 Initialisation des index spatiaux unifiés...")
        
        # Index pour les péages
        self.toll_index = SpatialIndexManager()
        
        # Index pour les entrées d'autoroute
        self.entry_index = MotorwayLinksSpatialIndex("ENTRY")
        
        # Index pour les sorties d'autoroute
        self.exit_index = MotorwayLinksSpatialIndex("EXIT")
        
        print("✅ Index spatiaux unifiés initialisés")
    
    # === MÉTHODES POUR LES PÉAGES ===
    
    def get_nearby_tolls(
        self, 
        route_coordinates: List[List[float]]
    ) -> List[TollBoothStation]:
        """
        Trouve les péages proches d'une route.
        
        Args:
            route_coordinates: Coordonnées de la route
            
        Returns:
            Liste des péages proches
        """
        return self.toll_index.query_bbox_candidates(route_coordinates)
    
    # === MÉTHODES POUR LES ENTRÉES ===
    
    def get_nearby_entries(
        self, 
        coordinates: List[float], 
        buffer_km: float = 0.2
    ) -> List[CompleteMotorwayLink]:
        """
        Trouve les entrées proches d'un point.
        
        Args:
            coordinates: [lon, lat] du point
            buffer_km: Distance de recherche en km
            
        Returns:
            Liste des entrées proches
        """
        return self.entry_index.query_nearby_links(coordinates, buffer_km)
    
    def get_entries_with_tolls(self) -> List[CompleteMotorwayLink]:
        """
        Retourne toutes les entrées qui ont des péages.
        
        Returns:
            Liste des entrées avec péages
        """
        return self.entry_index.get_links_with_tolls()
    
    def get_entries_along_route(
        self, 
        route_coordinates: List[List[float]], 
        buffer_km: float = 0.2
    ) -> List[CompleteMotorwayLink]:
        """
        Trouve les entrées le long d'une route.
        
        Args:
            route_coordinates: Coordonnées de la route
            buffer_km: Distance de recherche
            
        Returns:
            Liste des entrées le long de la route
        """
        return self.entry_index.query_links_along_route(route_coordinates, buffer_km)
    
    # === MÉTHODES POUR LES SORTIES ===
    
    def get_nearby_exits(
        self, 
        coordinates: List[float], 
        buffer_km: float = 0.2
    ) -> List[CompleteMotorwayLink]:
        """
        Trouve les sorties proches d'un point.
        
        Args:
            coordinates: [lon, lat] du point
            buffer_km: Distance de recherche en km
            
        Returns:
            Liste des sorties proches
        """
        return self.exit_index.query_nearby_links(coordinates, buffer_km)
    
    def get_exits_with_tolls(self) -> List[CompleteMotorwayLink]:
        """
        Retourne toutes les sorties qui ont des péages.
        
        Returns:
            Liste des sorties avec péages
        """
        return self.exit_index.get_links_with_tolls()
    
    # === MÉTHODES POUR REMPLACEMENT DE PÉAGES ===
    
    def find_replacement_entries_for_toll(
        self, 
        toll_coordinates: List[float], 
        buffer_km: float = 0.2
    ) -> List[CompleteMotorwayLink]:
        """
        Trouve les entrées candidates pour remplacer un péage.
        
        Args:
            toll_coordinates: Coordonnées du péage à remplacer
            buffer_km: Distance de recherche
            
        Returns:
            Liste des entrées candidates avec péages
        """
        # Trouver les entrées proches
        nearby_entries = self.get_nearby_entries(toll_coordinates, buffer_km)
        
        # Filtrer seulement celles qui ont des péages
        entries_with_tolls = [
            entry for entry in nearby_entries 
            if entry.has_toll()
        ]
        
        print(f"   🔄 Entrées de remplacement : {len(entries_with_tolls)} candidats "
              f"(sur {len(nearby_entries)} entrées proches)")
        
        return entries_with_tolls
    
    # === STATISTIQUES ===
    
    def get_unified_stats(self) -> Dict:
        """
        Retourne les statistiques de tous les index.
        
        Returns:
            Dictionnaire avec toutes les statistiques
        """
        return {
            'toll_index': self.toll_index.get_index_stats(),
            'entry_index': self.entry_index.get_index_stats(),
            'exit_index': self.exit_index.get_index_stats(),
            'all_indexes_ready': all([
                self.toll_index.index is not None,
                self.entry_index.index is not None,
                self.exit_index.index is not None
            ])
        }
    
    def rebuild_all_indexes(self) -> bool:
        """
        Reconstruit tous les index spatiaux.
        
        Returns:
            True si tous les index ont été reconstruits
        """
        results = [
            self.toll_index.rebuild_index(),
            self.entry_index.rebuild_index(),
            self.exit_index.rebuild_index()
        ]
        
        success = all(results)
        if success:
            print("✅ Tous les index spatiaux reconstruits")
        else:
            print("❌ Erreur lors de la reconstruction des index")
        
        return success
