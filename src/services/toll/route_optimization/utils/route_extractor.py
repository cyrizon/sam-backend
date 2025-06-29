"""
Route Extractor
===============

Utilitaires pour extraire les données des réponses de routes ORS.
Centralise l'extraction des coordonnées, instructions, distances, etc.
"""

from typing import List, Dict, Optional


class RouteExtractor:
    """Extracteur de données de routes ORS."""
    
    @staticmethod
    def extract_coordinates(route_response: Dict) -> List[List[float]]:
        """
        Extrait les coordonnées de la route depuis une réponse ORS.
        
        Args:
            route_response: Réponse ORS au format GeoJSON
            
        Returns:
            Liste des coordonnées [longitude, latitude]
        """
        if not route_response or "features" not in route_response:
            return []
        
        features = route_response["features"]
        if not features:
            return []
        
        feature = features[0]
        geometry = feature.get("geometry", {})
        
        if geometry.get("type") == "LineString":
            return geometry.get("coordinates", [])
        
        return []
    
    @staticmethod
    def extract_instructions(route_response: Dict) -> List[Dict]:
        """
        Extrait les instructions de navigation depuis une réponse ORS.
        
        Args:
            route_response: Réponse ORS au format GeoJSON
            
        Returns:
            Liste des instructions
        """
        if not route_response or "features" not in route_response:
            return []

        features = route_response["features"]
        if not features:
            return []

        feature = features[0]
        properties = feature.get("properties", {})
        
        # Essayer d'abord properties.instructions (format direct)
        instructions = properties.get("instructions", [])
        if instructions:
            return instructions
        
        # Si pas d'instructions directes, extraire depuis les segments
        segments = properties.get("segments", [])
        all_instructions = []
        
        for segment in segments:
            steps = segment.get("steps", [])
            for step in steps:
                all_instructions.append({
                    'instruction': step.get('instruction', ''),
                    'name': step.get('name', ''),
                    'distance': step.get('distance', 0),
                    'duration': step.get('duration', 0)
                })
        
        return all_instructions
    
    @staticmethod
    def extract_distance(route_response: Dict) -> float:
        """
        Extrait la distance totale depuis une réponse ORS.
        
        Args:
            route_response: Réponse ORS au format GeoJSON
            
        Returns:
            Distance en mètres, 0 si non trouvée
        """
        if not route_response or "features" not in route_response:
            return 0.0
        
        features = route_response["features"]
        if not features:
            return 0.0
        
        feature = features[0]
        properties = feature.get("properties", {})
        summary = properties.get("summary", {})
        
        return summary.get("distance", 0.0)
    
    @staticmethod
    def extract_duration(route_response: Dict) -> float:
        """
        Extrait la durée totale depuis une réponse ORS.
        
        Args:
            route_response: Réponse ORS au format GeoJSON
            
        Returns:
            Durée en secondes, 0 si non trouvée
        """
        if not route_response or "features" not in route_response:
            return 0.0
        
        features = route_response["features"]
        if not features:
            return 0.0
        
        feature = features[0]
        properties = feature.get("properties", {})
        summary = properties.get("summary", {})
        
        return summary.get("duration", 0.0)
    
    @staticmethod
    def extract_tollways_data(route_response: Dict) -> Optional[Dict]:
        """
        Extrait les données tollways depuis une réponse ORS.
        
        Args:
            route_response: Réponse ORS au format GeoJSON
            
        Returns:
            Données tollways ou None si non trouvées
        """
        if not route_response or "features" not in route_response:
            return None
        
        features = route_response["features"]
        if not features:
            return None
        
        feature = features[0]
        properties = feature.get("properties", {})
        extras = properties.get("extras", {})
        tollways_info = extras.get("tollways", {})
        
        if not tollways_info:
            return None
        
        segments = []
        values = tollways_info.get("values", [])
        
        for segment_info in values:
            if len(segment_info) >= 3:
                start_idx, end_idx, is_toll = segment_info
                segment = {
                    'start_waypoint': start_idx,
                    'end_waypoint': end_idx,
                    'is_toll': bool(is_toll),
                    'segment_type': 'toll' if is_toll else 'free'
                }
                segments.append(segment)
        
        return {
            'segments': segments,
            'total_segments': len(segments),
            'toll_segments': sum(1 for s in segments if s.get('is_toll', False)),
            'free_segments': sum(1 for s in segments if not s.get('is_toll', False))
        }
    
    @staticmethod
    def extract_route_bounds(route_response: Dict) -> Optional[Dict]:
        """
        Extrait les limites géographiques de la route.
        
        Args:
            route_response: Réponse ORS au format GeoJSON
            
        Returns:
            Dictionnaire avec min_lat, max_lat, min_lon, max_lon
        """
        coordinates = RouteExtractor.extract_coordinates(route_response)
        if not coordinates:
            return None
        
        lons = [coord[0] for coord in coordinates]
        lats = [coord[1] for coord in coordinates]
        
        return {
            'min_lon': min(lons),
            'max_lon': max(lons),
            'min_lat': min(lats),
            'max_lat': max(lats)
        }
