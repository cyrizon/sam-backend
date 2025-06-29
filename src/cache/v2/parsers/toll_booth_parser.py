"""
Toll Booth Parser
----------------

Parses toll booth data from OSM GeoJSON.
"""

import json
from typing import List, Dict, Optional

from ..models.toll_booth_station import TollBoothStation
from ..managers.open_tolls_manager import OpenTollsManager


class TollBoothParser:
    """Parser pour les données de péages OSM."""
    
    def __init__(self, geojson_file_path: str, open_tolls_manager: Optional[OpenTollsManager] = None):
        """
        Initialise le parser pour les toll booths.
        
        Args:
            geojson_file_path: Chemin vers toll_booths.geojson
            open_tolls_manager: Gestionnaire des péages ouverts (optionnel)
        """
        self.geojson_file_path = geojson_file_path
        self.open_tolls_manager = open_tolls_manager
        self.toll_booths: List[TollBoothStation] = []
    
    def parse(self) -> List[TollBoothStation]:
        """
        Parse le fichier toll_booths.geojson.
        
        Returns:
            List[TollBoothStation]: Liste des péages parsés
        """
        try:
            with open(self.geojson_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            features = data.get('features', [])
            print(f"🏪 Parsing {len(features)} toll booths...")
            
            for feature in features:
                toll_booth = self._parse_toll_booth_feature(feature)
                if toll_booth:
                    self.toll_booths.append(toll_booth)
            
            print(f"✅ Toll booths parsés: {len(self.toll_booths)}")
            return self.toll_booths
            
        except Exception as e:
            print(f"❌ Erreur lors du parsing des toll booths: {e}")
            return []
    
    def _parse_toll_booth_feature(self, feature: Dict) -> TollBoothStation:
        """Parse une feature de toll booth."""
        properties = feature.get('properties', {})
        geometry = feature.get('geometry', {})
        feature_id = feature.get('id', '')
        
        # Vérifier que c'est bien un toll booth
        if properties.get('barrier') != 'toll_booth':
            return None
        
        # Extraire les coordonnées
        coordinates = geometry.get('coordinates', [0.0, 0.0])
        
        # Déterminer le type de péage (ouvert ou fermé)
        toll_type = "F"  # Fermé par défaut
        if self.open_tolls_manager:
            toll_name = properties.get('name')
            if toll_name:
                toll_type = self.open_tolls_manager.get_toll_type(toll_name.strip())
        
        # Créer l'objet TollBoothStation
        return TollBoothStation(
            osm_id=feature_id,
            name=properties.get('name'),
            operator=properties.get('operator'),
            operator_ref=properties.get('operator:ref'),
            highway_ref=properties.get('highway:ref'),
            coordinates=coordinates,
            properties=properties,
            type=toll_type
        )
