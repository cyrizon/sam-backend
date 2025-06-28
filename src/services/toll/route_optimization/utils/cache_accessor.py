"""
Cache Accessor
==============

Accès unifié au système de cache pour récupérer péages, junctions et links.
Centralise l'accès aux données OSM pré-chargées et matchées.
"""

from typing import List, Optional, Dict
from src.cache.cached_osm_manager import cached_osm_data_manager
from src.cache.parsers.toll_matcher import MatchedToll


class CacheAccessor:
    """Accesseur unifié au cache OSM."""
    
    @staticmethod
    def get_toll_stations() -> List:
        """
        Récupère toutes les stations de péage du cache.
        
        Returns:
            Liste des stations de péage OSM
        """
        if not cached_osm_data_manager.is_loaded or not cached_osm_data_manager.osm_parser:
            return []
        
        if not hasattr(cached_osm_data_manager.osm_parser, 'toll_stations'):
            return []
        
        return cached_osm_data_manager.osm_parser.toll_stations or []
    
    @staticmethod
    def get_motorway_junctions() -> List:
        """
        Récupère toutes les junctions d'autoroute du cache.
        
        Returns:
            Liste des junctions d'autoroute OSM
        """
        if not cached_osm_data_manager.is_loaded or not cached_osm_data_manager.osm_parser:
            return []
        
        if not hasattr(cached_osm_data_manager.osm_parser, 'motorway_junctions'):
            return []
        
        return cached_osm_data_manager.osm_parser.motorway_junctions or []
    
    @staticmethod
    def get_motorway_links() -> List:
        """
        Récupère tous les liens d'autoroute du cache.
        
        Returns:
            Liste des liens d'autoroute OSM
        """
        if not cached_osm_data_manager.is_loaded or not cached_osm_data_manager.osm_parser:
            return []
        
        if not hasattr(cached_osm_data_manager.osm_parser, 'motorway_links'):
            return []
        
        return cached_osm_data_manager.osm_parser.motorway_links or []
    
    @staticmethod
    def get_matched_tolls() -> List[MatchedToll]:
        """
        Récupère les péages pré-matchés OSM/CSV du cache.
        
        Returns:
            Liste des péages pré-matchés avec données CSV
        """
        toll_stations = CacheAccessor.get_toll_stations()
        if not toll_stations:
            return []
        
        matched_tolls = []
        
        for toll_station in toll_stations:
            # Vérifier si le péage a été pré-matché avec les données CSV
            if hasattr(toll_station, 'csv_match') and toll_station.csv_match:
                # Péage pré-matché
                matched_toll = MatchedToll(
                    osm_id=toll_station.feature_id,
                    osm_name=toll_station.name,
                    osm_coordinates=toll_station.coordinates,
                    csv_id=toll_station.csv_match.get('id'),
                    csv_name=toll_station.csv_match.get('name'),
                    csv_role=toll_station.csv_match.get('role'),  # 'O' ou 'F'
                    csv_coordinates=toll_station.csv_match.get('coordinates'),
                    distance_m=toll_station.csv_match.get('distance_m', 0),
                    confidence=toll_station.csv_match.get('confidence', 1.0)
                )
                matched_tolls.append(matched_toll)
            else:
                # Péage OSM non matché -> considéré comme fermé (csv_role='F')
                matched_toll = MatchedToll(
                    osm_id=toll_station.feature_id,
                    osm_name=toll_station.name,
                    osm_coordinates=toll_station.coordinates,
                    csv_id=None,
                    csv_name=None,
                    csv_role='F',  # Fermé par défaut si non matché
                    csv_coordinates=None,
                    distance_m=0,
                    confidence=0.0
                )
                matched_tolls.append(matched_toll)
        
        return matched_tolls
    
    @staticmethod
    def is_cache_available() -> bool:
        """
        Vérifie si le cache OSM est disponible et chargé.
        
        Returns:
            True si le cache est disponible, False sinon
        """
        return (cached_osm_data_manager.is_loaded and 
                cached_osm_data_manager.osm_parser is not None and
                hasattr(cached_osm_data_manager.osm_parser, 'toll_stations'))
    
    @staticmethod
    def get_cache_stats() -> Dict:
        """
        Récupère les statistiques du cache.
        
        Returns:
            Dictionnaire avec les statistiques du cache
        """
        if not CacheAccessor.is_cache_available():
            return {
                'available': False,
                'toll_stations': 0,
                'motorway_junctions': 0,
                'motorway_links': 0,
                'matched_tolls': 0
            }
        
        toll_stations = CacheAccessor.get_toll_stations()
        motorway_junctions = CacheAccessor.get_motorway_junctions()
        motorway_links = CacheAccessor.get_motorway_links()
        matched_tolls = CacheAccessor.get_matched_tolls()
        
        return {
            'available': True,
            'toll_stations': len(toll_stations),
            'motorway_junctions': len(motorway_junctions),
            'motorway_links': len(motorway_links),
            'matched_tolls': len(matched_tolls)
        }
