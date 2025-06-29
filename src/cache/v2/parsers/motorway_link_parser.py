"""
Motorway Link Parser
-------------------

Parses motorway link data from OSM GeoJSON.
"""

import json
from typing import List, Dict

from ..models.motorway_link import MotorwayLink
from ..models.link_types import LinkType


class MotorwayLinkParser:
    """Parser pour les données de motorway_link OSM."""
    
    def __init__(self, geojson_file_path: str, link_type: LinkType):
        """
        Initialise le parser pour les motorway links.
        
        Args:
            geojson_file_path: Chemin vers le fichier GeoJSON
            link_type: Type de liens (ENTRY, EXIT, INDETERMINATE)
        """
        self.geojson_file_path = geojson_file_path
        self.link_type = link_type
        self.motorway_links: List[MotorwayLink] = []
    
    def parse(self) -> List[MotorwayLink]:
        """
        Parse le fichier motorway_link GeoJSON.
        
        Returns:
            List[MotorwayLink]: Liste des liens parsés
        """
        try:
            with open(self.geojson_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            features = data.get('features', [])
            print(f"🛣️ Parsing {len(features)} motorway links ({self.link_type.value})...")
            
            for feature in features:
                motorway_link = self._parse_motorway_link_feature(feature)
                if motorway_link:
                    self.motorway_links.append(motorway_link)
            
            print(f"✅ Motorway links parsés ({self.link_type.value}): {len(self.motorway_links)}")
            return self.motorway_links
            
        except Exception as e:
            print(f"❌ Erreur lors du parsing des motorway links ({self.link_type.value}): {e}")
            return []
    
    def _parse_motorway_link_feature(self, feature: Dict) -> MotorwayLink:
        """Parse une feature de motorway link."""
        properties = feature.get('properties', {})
        geometry = feature.get('geometry', {})
        feature_id = feature.get('id', '')
        
        # Vérifier que c'est bien un motorway_link
        if properties.get('highway') != 'motorway_link':
            return None
        
        # Extraire les coordonnées (LineString)
        coordinates = geometry.get('coordinates', [])
        if not coordinates:
            return None
        
        # Extraire la destination si disponible
        destination = properties.get('destination')
        
        # Créer l'objet MotorwayLink
        return MotorwayLink(
            way_id=feature_id,
            link_type=self.link_type,
            coordinates=coordinates,
            properties=properties,
            destination=destination
        )
