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
        # Extraire toutes les coordonnées, instructions et assembler
        all_coords = []
        all_instructions = []
        total_distance = 0
        total_duration = 0        
        for i, segment in enumerate(segments):
            coords = RouteUtils.extract_route_coordinates(segment)
            instructions = RouteUtils.extract_instructions(segment)
            distance = RouteUtils.extract_distance(segment)
            duration = RouteUtils.extract_duration(segment)
            
            # Pour le premier segment
            if i == 0:
                all_coords.extend(coords)
                # Supprimer la dernière instruction (arrivée) sauf si c'est le seul segment
                if len(segments) > 1 and instructions:
                    all_instructions.extend(instructions[:-1])  # Enlever la dernière instruction
                else:
                    all_instructions.extend(instructions)  # Garder toutes si c'est le seul segment
            else:
                # Pour les segments suivants, éviter le point dupliqué
                all_coords.extend(coords[1:])
                
                # Ajuster les instructions en sautant la première (point de départ dupliqué)
                # et la dernière (arrivée) sauf pour le dernier segment
                if instructions and len(instructions) > 1:
                    start_idx = 1  # Sauter la première instruction (point de départ dupliqué)
                    end_idx = len(instructions)
                    
                    # Si ce n'est pas le dernier segment, supprimer aussi la dernière instruction
                    if i < len(segments) - 1:
                        end_idx = -1  # Enlever la dernière instruction (arrivée)
                    
                    all_instructions.extend(instructions[start_idx:end_idx])
                elif instructions and i == len(segments) - 1:
                    # Pour le dernier segment, même avec une seule instruction, on la garde
                    all_instructions.extend(instructions[1:] if len(instructions) > 1 else instructions)
            
            total_distance += distance
            total_duration += duration
            print(f"   📍 Segment {i+1} : {distance/1000:.1f} km ajouté")
        # Construire la route finale
        final_route = RouteAssembler._build_route_geojson(
            all_coords, total_distance, total_duration, selected_tolls, all_instructions
        )
        
        print(f"✅ Route assemblée : {total_distance/1000:.1f} km")
        print(f"   📍 Péages utilisés : {[toll.effective_name for toll in selected_tolls]}")
        
        return RouteAssembler._build_result_response(            final_route, target_tolls, selected_tolls, len(segments), 
            total_distance, total_duration
        )
    
    @staticmethod
    def _build_route_geojson(
        coordinates: List[List[float]], 
        distance: float, 
        duration: float, 
        selected_tolls: List[MatchedToll],
        instructions: List[Dict] = None
    ) -> Dict:
        """
        Construit le GeoJSON de la route finale.
        
        Args:
            coordinates: Coordonnées de la route
            distance: Distance totale
            duration: Durée totale
            selected_tolls: Péages sélectionnés
            instructions: Instructions de navigation
            
        Returns:
            Dict: GeoJSON de la route
        """
        properties = {
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
        
        # Ajouter les instructions si disponibles
        if instructions:
            properties["instructions"] = instructions
        
        return {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coordinates},
                "properties": properties
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
        """        # Extraire les instructions du route GeoJSON pour les rendre facilement accessibles
        instructions = None
        if 'features' in route and route['features']:
            feature_props = route['features'][0].get('properties', {})
            instructions = feature_props.get('instructions', [])        
        return {
            'route': route,
            'target_tolls': target_tolls,
            'found_solution': 'intelligent_success',
            'respects_constraint': True,
            'strategy_used': 'intelligent_segmentation',
            'distance': distance,
            'duration': duration,
            'instructions': instructions,  # Instructions au niveau principal
            'segments': {
                'count': segments_count,
                'toll_segments': segments_count - 1 if segments_count > 1 else 0,
                'free_segments': 1 if segments_count > 1 else 0
            },
            'toll_info': {
                'selected_tolls': [toll.effective_name for toll in selected_tolls],
                'toll_systems': [
                    "ouvert" if toll.is_open_system else "fermé" 
                    for toll in selected_tolls
                ],
                'coordinates': [
                    {'name': toll.effective_name, 'lat': toll.osm_coordinates[1], 'lon': toll.osm_coordinates[0]}
                    for toll in selected_tolls
                ]
            }
        }
