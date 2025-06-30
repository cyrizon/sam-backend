"""
Motorway Segments Parser
-----------------------

Parser for motorway segment GeoJSON files (entries, exits, indeterminate).
"""

import json
from typing import List, Dict, Any, Optional

from ..models.motorway_link import MotorwayLink
from ..models.link_types import LinkType


class MotorwaySegmentsParser:
    """Parser pour les fichiers GeoJSON de segments motorway."""
    
    def __init__(self):
        """Initialise le parser."""
        pass
    
    def parse_segments(self, geojson_path: str, link_type: LinkType) -> List[MotorwayLink]:
        """
        Parse un fichier GeoJSON de segments motorway.
        
        Args:
            geojson_path: Chemin vers le fichier GeoJSON
            link_type: Type de lien (ENTRY, EXIT, INDETERMINATE)
            
        Returns:
            List[MotorwayLink]: Liste des segments parsés
        """
        try:
            with open(geojson_path, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
            
            segments = []
            features = geojson_data.get('features', [])
            
            for feature in features:
                segment = self._parse_feature(feature, link_type)
                if segment:
                    segments.append(segment)
            
            print(f"   📄 Fichier parsé: {geojson_path} -> {len(segments)} segments")
            return segments
            
        except Exception as e:
            print(f"❌ Erreur lors du parsing de {geojson_path}: {e}")
            return []
    
    def _parse_feature(self, feature: Dict[str, Any], link_type: LinkType) -> Optional[MotorwayLink]:
        """
        Parse une feature GeoJSON en MotorwayLink.
        
        Args:
            feature: Feature GeoJSON
            link_type: Type de lien
            
        Returns:
            MotorwayLink ou None si erreur
        """
        try:
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            
            # Extraire le way_id depuis @id (format: "way/123456")
            osm_id = properties.get('@id', '')
            if osm_id.startswith('way/'):
                way_id = osm_id.replace('way/', '')
            else:
                # Fallback vers d'autres champs possibles
                way_id = str(properties.get('way_id', properties.get('id', f'unknown_{hash(str(feature))%10000}')))
            
            # Extraire les coordonnées
            coordinates = []
            if geometry.get('type') == 'LineString':
                coordinates = geometry.get('coordinates', [])
            elif geometry.get('type') == 'MultiLineString':
                # Pour MultiLineString, prendre la première ligne
                multi_coords = geometry.get('coordinates', [])
                if multi_coords:
                    coordinates = multi_coords[0]
            
            if not coordinates:
                print(f"   ⚠️  Coordonnées manquantes pour {way_id}")
                return None
            
            # Extraire la destination si disponible
            destination = properties.get('destination')
            if destination and isinstance(destination, list):
                destination = ';'.join(destination)
            
            # Créer le segment
            segment = MotorwayLink(
                way_id=way_id,
                link_type=link_type,
                coordinates=coordinates,
                properties=properties,
                destination=destination
            )
            
            return segment
            
        except Exception as e:
            print(f"   ⚠️  Erreur lors du parsing d'une feature: {e}")
            return None
    
    def parse_all_segments(
        self, 
        entries_path: str, 
        exits_path: str, 
        indeterminates_path: str
    ) -> tuple[List[MotorwayLink], List[MotorwayLink], List[MotorwayLink]]:
        """
        Parse tous les fichiers de segments d'un coup.
        
        Args:
            entries_path: Chemin vers le fichier des entrées
            exits_path: Chemin vers le fichier des sorties
            indeterminates_path: Chemin vers le fichier des indéterminés
            
        Returns:
            Tuple[entrées, sorties, indéterminés]
        """
        entries = self.parse_segments(entries_path, LinkType.ENTRY)
        exits = self.parse_segments(exits_path, LinkType.EXIT)
        indeterminates = self.parse_segments(indeterminates_path, LinkType.INDETERMINATE)
        
        return entries, exits, indeterminates
    
    def validate_segment_data(self, segments: List[MotorwayLink]) -> Dict[str, Any]:
        """
        Valide les données des segments et retourne des statistiques.
        
        Args:
            segments: Liste des segments à valider
            
        Returns:
            Dict avec statistiques de validation
        """
        stats = {
            'total_segments': len(segments),
            'valid_segments': 0,
            'invalid_segments': 0,
            'segments_with_destination': 0,
            'unique_way_ids': set(),
            'duplicate_way_ids': set(),
            'coordinate_issues': []
        }
        
        way_id_counts = {}
        
        for segment in segments:
            # Compter les way_id
            if segment.way_id in way_id_counts:
                way_id_counts[segment.way_id] += 1
                stats['duplicate_way_ids'].add(segment.way_id)
            else:
                way_id_counts[segment.way_id] = 1
                stats['unique_way_ids'].add(segment.way_id)
            
            # Vérifier les coordonnées
            if not segment.coordinates or len(segment.coordinates) < 2:
                stats['coordinate_issues'].append(segment.way_id)
                stats['invalid_segments'] += 1
            else:
                stats['valid_segments'] += 1
            
            # Vérifier la destination
            if segment.destination:
                stats['segments_with_destination'] += 1
        
        # Finaliser les statistiques
        stats['unique_way_ids'] = len(stats['unique_way_ids'])
        stats['duplicate_way_ids'] = len(stats['duplicate_way_ids'])
        stats['coordinate_issues'] = len(stats['coordinate_issues'])
        
        return stats
