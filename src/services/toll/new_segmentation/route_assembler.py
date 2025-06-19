"""
route_assembler.py
-----------------

Module pour assembler les segments de route calculés.
Responsable de l'assemblage final et du formatage des résultats.
"""

import os
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
        
        return RouteAssembler._build_result_response(
            final_route, target_tolls, selected_tolls, len(segments), 
            total_distance, total_duration, all_instructions
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
            }
        }
        
        # Note: instructions, selected_tolls, toll_systems sont maintenant uniquement 
        # dans la réponse racine pour éviter la duplication
        
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
        duration: float,
        instructions: List[Dict] = None
    ) -> Dict:
        """
        Construit la réponse finale avec toutes les métadonnées.
        
        Args:            route: Route GeoJSON
            target_tolls: Nombre de péages demandé
            selected_tolls: Péages sélectionnés
            segments_count: Nombre de segments
            distance: Distance totale
            duration: Durée totale
            instructions: Instructions de navigation
            
        Returns:
            Dict: Réponse complète formatée
        """
        
        # Note: les instructions sont passées directement en paramètre pour éviter la duplication
        
        # Calculer les informations détaillées des péages (comme dans /api/route/)
        detailed_tolls = []
        total_toll_cost = 0
        if route and 'features' in route and route['features']:
            try:
                from src.services.toll_locator import locate_tolls
                from src.services.toll_cost import add_marginal_cost
                
                csv_path = os.path.join(os.path.dirname(__file__), "../../../data/barriers.csv")
                tolls_dict = locate_tolls(route, csv_path, buffer_m=120)
                detailed_tolls = add_marginal_cost(tolls_dict["on_route"], veh_class="c1")
                total_toll_cost = sum(t.get("cost", 0) for t in detailed_tolls)
                
                print(f"💰 Coût total des péages : {total_toll_cost}€")
                print(f"🏧 Péages détaillés : {len(detailed_tolls)} trouvés")
                
            except Exception as e:
                print(f"⚠️ Erreur calcul coût péages : {e}")
                detailed_tolls = []
                total_toll_cost = 0        
        result = {
            'route': route,
            'target_tolls': target_tolls,
            'found_solution': 'intelligent_success',
            'respects_constraint': True,
            'strategy_used': 'intelligent_segmentation',
            'distance': distance,
            'duration': duration,
            'instructions': instructions,  # Instructions au niveau principal
            'cost': total_toll_cost,  # Coût total des péages (comme /api/route/)
            'toll_count': len(detailed_tolls),  # Nombre de péages (comme /api/route/)
            'tolls': detailed_tolls,  # Détails des péages (comme /api/tolls)
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
        
        return result
