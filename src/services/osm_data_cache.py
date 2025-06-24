"""
osm_data_cache.py
-----------------

Cache global pour les données OSM (motorway_junction, motorway_link, toll_station).
Chargé une seule fois au démarrage de l'application.
"""

import os
from src.services.toll.new_segmentation.osm_data_parser import OSMDataParser

class GlobalOSMDataCache:
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
        if geojson_path is not None:
            self._geojson_path = geojson_path
        if not self._geojson_path:
            # Chercher dans data/osm_export_toll.geojson à la racine du projet
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self._geojson_path = os.path.join(project_root, 'data', 'osm_export_toll.geojson')
        print(f"🚦 Initialisation du cache OSM depuis : {self._geojson_path}")
        self._osm_parser = OSMDataParser(self._geojson_path)
        success = self._osm_parser.load_and_parse()
        if not success:
            raise RuntimeError("Erreur lors du chargement des données OSM !")
        self._initialized = True
        print("✅ Cache OSM initialisé avec succès!")

    @property
    def motorway_junctions(self):
        if not self._initialized:
            raise RuntimeError("Cache OSM non initialisé ! Appelez initialize() d'abord.")
        return self._osm_parser.motorway_junctions

    @property
    def motorway_links(self):
        if not self._initialized:
            raise RuntimeError("Cache OSM non initialisé ! Appelez initialize() d'abord.")
        return self._osm_parser.motorway_links

    @property
    def toll_stations(self):
        if not self._initialized:
            raise RuntimeError("Cache OSM non initialisé ! Appelez initialize() d'abord.")
        return self._osm_parser.toll_stations

    def get_stats(self):
        if not self._initialized:
            return {"status": "non_initialized"}
        return {
            "status": "initialized",
            "junctions_count": len(self.motorway_junctions),
            "links_count": len(self.motorway_links),
            "toll_stations_count": len(self.toll_stations)
        }

# Instance globale unique
osm_data_cache = GlobalOSMDataCache()
