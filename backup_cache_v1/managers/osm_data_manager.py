"""
OSM Data Manager
---------------

Manages OSM data cache including junctions, links, and toll stations.
Refactored from osm_data_cache.py with <300 lines.
"""

import os
from typing import List

from ..models.motorway_junction import MotorwayJunction
from ..models.motorway_link import MotorwayLink  
from ..models.toll_station import TollStation
from ..parsers.osm_parser import OSMParser


class OSMDataManager:
    """
    Cache global pour les données OSM initialisé au démarrage de l'application.
    """
    
    def __init__(self):
        self._osm_parser = None
        self._initialized = False
        self._geojson_path = None

    def initialize(self, geojson_path=None):
        """
        Initialise le cache OSM au démarrage de l'application.
        """
        if self._initialized:
            print("⚠️ Cache OSM déjà initialisé, skip...")
            return
            
        self._set_geojson_path(geojson_path)
        
        print(f"🚦 Initialisation du cache OSM depuis : {self._geojson_path}")
        
        try:
            self._osm_parser = OSMParser(self._geojson_path)
            success = self._osm_parser.load_and_parse()
            
            if not success:
                raise RuntimeError("Erreur lors du chargement des données OSM !")
            
            self._initialized = True
            print("✅ Cache OSM initialisé avec succès!")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation du cache OSM: {e}")
            raise
    
    def _set_geojson_path(self, geojson_path):
        """Définit le chemin du fichier GeoJSON."""
        if geojson_path is not None:
            self._geojson_path = geojson_path
        elif not self._geojson_path:
            # Chercher dans data/osm_export_toll.geojson à la racine du projet
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            self._geojson_path = os.path.join(project_root, 'data', 'osm_export_toll.geojson')

    @property
    def motorway_junctions(self) -> List[MotorwayJunction]:
        """Accès aux motorway_junctions"""
        if not self._initialized:
            raise RuntimeError("Cache OSM non initialisé ! Appelez initialize() d'abord.")
        return self._osm_parser.motorway_junctions

    @property
    def motorway_links(self) -> List[MotorwayLink]:
        """Accès aux motorway_links"""
        if not self._initialized:
            raise RuntimeError("Cache OSM non initialisé ! Appelez initialize() d'abord.")
        return self._osm_parser.motorway_links

    @property
    def toll_stations(self) -> List[TollStation]:
        """Accès aux toll_stations"""
        if not self._initialized:
            raise RuntimeError("Cache OSM non initialisé ! Appelez initialize() d'abord.")
        return self._osm_parser.toll_stations

    def get_stats(self):
        """Statistiques du cache OSM"""
        if not self._initialized:
            return {"status": "non_initialized"}
        
        return {
            "status": "initialized",
            "junctions_count": len(self.motorway_junctions),
            "links_count": len(self.motorway_links),
            "toll_stations_count": len(self.toll_stations)
        }
    
    def is_initialized(self) -> bool:
        """Retourne True si le cache est initialisé."""
        return self._initialized
