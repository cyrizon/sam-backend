"""
tollway_extractor.py
-------------------

Module responsable de l'extraction et de l'analyse des informations de péages
depuis les données ORS (extra_info: tollways).

Responsabilité unique : transformer les données brutes ORS en segments exploitables.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TollwaySegment:
    """Représente un segment de route avec ou sans péage."""
    start_index: int
    end_index: int
    has_toll: bool
    coordinates: List[List[float]] = None
    
    @property
    def length(self) -> int:
        """Retourne la longueur du segment en nombre de points."""
        return self.end_index - self.start_index
    
    def __repr__(self):
        toll_status = "TOLL" if self.has_toll else "FREE"
        return f"TollwaySegment({self.start_index}-{self.end_index}, {toll_status})"


class TollwayExtractor:
    """
    Extracteur d'informations de péages depuis les données ORS.
    
    Transforme les données tollways brutes en segments structurés 
    avec leurs coordonnées géographiques correspondantes.
    """
    
    @staticmethod
    def extract_tollway_data(ors_response: dict) -> Optional[Dict]:
        """
        Extrait les données tollways depuis une réponse ORS.
        
        Args:
            ors_response: Réponse JSON complète d'ORS
            
        Returns:
            dict: Données tollways extraites ou None si non trouvées
            
        Structure retournée:
        {
            'summary': [...],
            'values': [...],
            'coordinates': [...]  # géométrie complète de la route
        }
        """
        try:
            feature = ors_response.get('features', [{}])[0]
            properties = feature.get('properties', {})
            extras = properties.get('extras', {})
            tollways_data = extras.get('tollways', {})
            
            if not tollways_data or 'values' not in tollways_data:
                return None
                
            # Extraire aussi la géométrie complète
            geometry = feature.get('geometry', {})
            coordinates = geometry.get('coordinates', [])
            
            return {
                'summary': tollways_data.get('summary', []),
                'values': tollways_data.get('values', []),
                'coordinates': coordinates
            }
            
        except (KeyError, IndexError, TypeError):
            return None
    
    @staticmethod
    def parse_segments(tollway_data: Dict) -> List[TollwaySegment]:
        """
        Parse les données tollways en segments structurés.
        
        Args:
            tollway_data: Données tollways extraites par extract_tollway_data
            
        Returns:
            List[TollwaySegment]: Liste des segments avec leurs propriétés
        """
        if not tollway_data or 'values' not in tollway_data:
            return []
            
        values = tollway_data['values']
        coordinates = tollway_data['coordinates']
        segments = []
        
        for segment_data in values:
            if len(segment_data) >= 3:
                start_idx, end_idx, toll_value = segment_data[0], segment_data[1], segment_data[2]
                
                # Extraire les coordonnées du segment
                segment_coords = None
                if coordinates and 0 <= start_idx < len(coordinates) and 0 <= end_idx < len(coordinates):
                    # S'assurer que start_idx <= end_idx
                    if start_idx <= end_idx:
                        segment_coords = coordinates[start_idx:end_idx + 1]
                    else:
                        # Inverser si nécessaire
                        segment_coords = coordinates[end_idx:start_idx + 1]
                
                segment = TollwaySegment(
                    start_index=start_idx,
                    end_index=end_idx,
                    has_toll=(toll_value == 1),
                    coordinates=segment_coords
                )
                segments.append(segment)
        
        return segments
    
    @staticmethod
    def get_toll_segments_only(segments: List[TollwaySegment]) -> List[TollwaySegment]:
        """
        Filtre pour ne garder que les segments avec péages.
        
        Args:
            segments: Liste complète des segments
            
        Returns:
            List[TollwaySegment]: Segments avec péages uniquement
        """
        return [seg for seg in segments if seg.has_toll]
    
    @staticmethod
    def get_segment_coordinates(segment: TollwaySegment, full_coordinates: List[List[float]]) -> List[List[float]]:
        """
        Récupère les coordonnées géographiques d'un segment spécifique.
        
        Args:
            segment: Segment dont on veut les coordonnées
            full_coordinates: Coordonnées complètes de la route
            
        Returns:
            List[List[float]]: Coordonnées du segment [longitude, latitude]
        """
        if not full_coordinates or segment.start_index >= len(full_coordinates):
            return []
            
        end_idx = min(segment.end_index + 1, len(full_coordinates))
        return full_coordinates[segment.start_index:end_idx]


class TollwayAnalyzer:
    """
    Analyseur pour les données de péages extraites.
    
    Fournit des métriques et analyses sur les segments de péages.
    """
    
    @staticmethod
    def count_toll_segments(segments: List[TollwaySegment]) -> int:
        """Compte le nombre de segments avec péages."""
        return len([seg for seg in segments if seg.has_toll])
    
    @staticmethod
    def get_toll_summary(tollway_data: Dict) -> Dict:
        """
        Retourne un résumé des coûts de péages depuis les données summary.
        
        Args:
            tollway_data: Données tollways complètes
            
        Returns:
            dict: Résumé des coûts et distances
        """
        summary = tollway_data.get('summary', [])
        
        total_cost = 0
        total_toll_distance = 0
        total_free_distance = 0
        
        for item in summary:
            if item.get('value') == 1:  # Segment avec péage
                total_cost += item.get('amount', 0)
                total_toll_distance += item.get('distance', 0)
            else:  # Segment gratuit
                total_free_distance += item.get('distance', 0)
        
        return {
            'total_cost': total_cost,
            'toll_distance_m': total_toll_distance,
            'free_distance_m': total_free_distance,
            'total_distance_m': total_toll_distance + total_free_distance
        }
