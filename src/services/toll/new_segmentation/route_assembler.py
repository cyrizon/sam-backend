"""
route_assembler.py
-----------------

Module pour assembler les segments de route calculés.
Responsable de l'assemblage final et du formatage des résultats.
"""

from typing import List, Dict
from .toll_matcher import MatchedToll
from .intelligent_segmentation_helpers import RouteUtils


class RouteAssembler:
    """
    Classe responsable de l'assemblage des segments de route
    et du formatage des résultats finaux.
    """
    
    @staticmethod
    def assemble_final_route_multi(
        segments: List[Dict], 
        target_tolls: int, 
        selected_tolls: List[MatchedToll]
    ) -> Dict:
        """
        Assemble la route finale multi-segments.
        
        Args:
            segments: Liste des segments calculés
            target_tolls: Nombre de péages demandé
            selected_tolls: Péages sélectionnés
            
        Returns:
            Dict: Route finale assemblée avec métadonnées
        """
        print("🔧 Assemblage de la route finale multi-segments...")
        
        # Extraire toutes les coordonnées et assembler
        all_coords = []
        total_distance = 0
        total_duration = 0
        
        for i, segment in enumerate(segments):
            coords = RouteUtils.extract_route_coordinates(segment)
            distance = RouteUtils.extract_distance(segment)
            duration = RouteUtils.extract_duration(segment)
            
            # Pour le premier segment, prendre toutes les coordonnées
            if i == 0:
                all_coords.extend(coords)
            else:
                # Pour les segments suivants, éviter le point dupliqué
                all_coords.extend(coords[1:])
            
            total_distance += distance
            total_duration += duration
            print(f"   📍 Segment {i+1} : {distance/1000:.1f} km ajouté")
        
        # Construire la route finale
        final_route = RouteAssembler._build_route_geojson(
            all_coords, total_distance, total_duration, selected_tolls
        )
        
        print(f"✅ Route assemblée : {total_distance/1000:.1f} km")
        print(f"   📍 Péages utilisés : {[toll.effective_name for toll in selected_tolls]}")
        
        return RouteAssembler._build_result_response(
            final_route, target_tolls, selected_tolls, len(segments), 
            total_distance, total_duration
        )
    
    @staticmethod
    def _build_route_geojson(
        coordinates: List[List[float]], 
        distance: float, 
        duration: float, 
        selected_tolls: List[MatchedToll]
    ) -> Dict:
        """
        Construit le GeoJSON de la route finale.
        
        Args:
            coordinates: Coordonnées de la route
            distance: Distance totale
            duration: Durée totale
            selected_tolls: Péages sélectionnés
            
        Returns:
            Dict: GeoJSON de la route
        """
        return {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coordinates},
                "properties": {
                    "summary": {
                        "distance": distance,
                        "duration": duration
                    },
                    "selected_tolls": [toll.effective_name for toll in selected_tolls],
                    "toll_systems": [
                        "ouvert" if toll.is_open_system else "fermé" 
                        for toll in selected_tolls
                    ]
                }
            }]
        }
    
    @staticmethod
    def _build_result_response(
        route: Dict, 
        target_tolls: int, 
        selected_tolls: List[MatchedToll], 
        segments_count: int,
        distance: float, 
        duration: float
    ) -> Dict:
        """
        Construit la réponse finale avec toutes les métadonnées.
        
        Args:
            route: Route GeoJSON
            target_tolls: Nombre de péages demandé
            selected_tolls: Péages sélectionnés
            segments_count: Nombre de segments
            distance: Distance totale
            duration: Durée totale
            
        Returns:
            Dict: Réponse complète formatée
        """
        return {
            'route': route,
            'status': 'intelligent_segmentation_success',
            'target_tolls': target_tolls,
            'actual_tolls': len(selected_tolls),
            'strategy': 'intelligent_segmentation_v2',
            'segments_count': segments_count,
            'distance': distance,
            'duration': duration,
            'used_tolls': [
                {
                    'name': toll.effective_name,
                    'system': 'ouvert' if toll.is_open_system else 'fermé',
                    'coordinates': toll.osm_coordinates
                }
                for toll in selected_tolls
            ]
        }
