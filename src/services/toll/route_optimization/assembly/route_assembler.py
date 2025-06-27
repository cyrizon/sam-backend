"""
Route Assembler
===============

Module pour assembler les segments de route calculés.
Version simplifiée pour l'optimiseur de routes.
"""

from typing import List, Dict
from ..utils.route_extractor import RouteExtractor


class RouteAssembler:
    """Assembleur de routes simplifié."""
    
    @staticmethod
    def assemble_final_route(
        segments: List[Dict], 
        target_tolls: int, 
        selected_tolls: List = None
    ) -> Dict:
        """
        Assemble la route finale à partir des segments calculés.
        
        Args:
            segments: Liste des segments calculés
            target_tolls: Nombre de péages demandé
            selected_tolls: Péages sélectionnés (optionnel)
            
        Returns:
            Route finale assemblée avec métadonnées
        """
        print("🔧 Étape 8: Assemblage de la route finale...")
        print(f"   📊 Assemblage de {len(segments)} segments")
        
        if not segments:
            print("❌ Aucun segment à assembler")
            return None
        
        # Extraire et assembler les données de tous les segments
        all_coords = []
        all_instructions = []
        total_distance = 0
        total_duration = 0
        
        for i, segment in enumerate(segments):
            coords = RouteExtractor.extract_coordinates(segment)
            instructions = RouteExtractor.extract_instructions(segment)
            distance = RouteExtractor.extract_distance(segment)
            duration = RouteExtractor.extract_duration(segment)
            
            print(f"   📍 Segment {i+1}: {distance/1000:.1f}km, {len(coords)} points")
            
            # Premier segment : ajouter tous les points
            if i == 0:
                all_coords.extend(coords)
                all_instructions.extend(instructions)
            else:
                # Segments suivants : éviter la duplication du premier point
                all_coords.extend(coords[1:] if coords else [])
                
                # Ajuster les instructions pour éviter les doublons
                if instructions:
                    # Sauter la première instruction (point de départ dupliqué)
                    adjusted_instructions = instructions[1:] if len(instructions) > 1 else []
                    all_instructions.extend(adjusted_instructions)
            
            total_distance += distance
            total_duration += duration
        
        # Construire la route finale
        final_route = RouteAssembler._build_route_geojson(
            all_coords, total_distance, total_duration, all_instructions
        )
        
        # Calculer les coûts de péages
        toll_cost, toll_details = RouteAssembler._calculate_toll_costs(final_route)
        
        print(f"✅ Route assemblée: {total_distance/1000:.1f}km, "
              f"{total_duration/60:.1f}min, {toll_cost}€")
        
        return {
            'route': final_route,
            'target_tolls': target_tolls,
            'found_solution': 'optimization_success',
            'respects_constraint': True,
            'strategy_used': 'intelligent_optimization',
            'distance': total_distance,
            'duration': total_duration,
            'instructions': all_instructions,
            'cost': toll_cost,
            'toll_count': len(toll_details),
            'tolls': toll_details,
            'segments': {
                'count': len(segments),
                'toll_segments': len([s for s in segments if s.get('has_tolls', False)]),
                'free_segments': len([s for s in segments if not s.get('has_tolls', False)])
            },
            'toll_info': {
                'selected_tolls': [t.get('name', 'Inconnu') for t in (selected_tolls or [])],
                'toll_systems': [],
                'coordinates': []
            }
        }
    
    @staticmethod
    def _build_route_geojson(
        coordinates: List[List[float]], 
        distance: float, 
        duration: float,
        instructions: List[Dict] = None
    ) -> Dict:
        """
        Construit le GeoJSON de la route finale.
        
        Args:
            coordinates: Coordonnées de la route
            distance: Distance totale en mètres
            duration: Durée totale en secondes
            instructions: Instructions de navigation
            
        Returns:
            GeoJSON de la route
        """
        properties = {
            "summary": {
                "distance": distance,
                "duration": duration
            }
        }
        
        if instructions:
            properties["instructions"] = instructions
        
        return {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "LineString", 
                    "coordinates": coordinates
                },
                "properties": properties
            }]
        }
    
    @staticmethod
    def _calculate_toll_costs(route: Dict) -> tuple:
        """
        Calcule les coûts de péages pour la route assemblée.
        
        Args:
            route: Route au format GeoJSON
            
        Returns:
            Tuple (coût_total, détails_péages)
        """
        try:
            from src.services.toll_locator import locate_tolls
            from src.services.toll_cost import add_marginal_cost
            
            # Localiser les péages sur la route
            tolls_dict = locate_tolls(route, buffer_m=1.0, veh_class="c1")
            
            # Calculer les coûts
            detailed_tolls = add_marginal_cost(tolls_dict["on_route"], veh_class="c1")
            total_cost = sum(toll.get("cost", 0) for toll in detailed_tolls)
            
            return total_cost, detailed_tolls
            
        except Exception as e:
            print(f"⚠️ Erreur calcul coûts péages : {e}")
            return 0.0, []
    
    @staticmethod
    def format_base_route_as_result(base_route: Dict, target_tolls: int) -> Dict:
        """
        Formate une route de base comme résultat final.
        Utilisé quand l'optimisation n'est pas nécessaire.
        
        Args:
            base_route: Route de base
            target_tolls: Nombre de péages demandé
            
        Returns:
            Route formatée comme résultat d'optimisation
        """
        distance = RouteExtractor.extract_distance(base_route)
        duration = RouteExtractor.extract_duration(base_route)
        instructions = RouteExtractor.extract_instructions(base_route)
        
        # Calculer les coûts de péages
        toll_cost, toll_details = RouteAssembler._calculate_toll_costs(base_route)
        
        return {
            'route': base_route,
            'target_tolls': target_tolls,
            'found_solution': 'base_route_sufficient',
            'respects_constraint': True,
            'strategy_used': 'base_route',
            'distance': distance,
            'duration': duration,
            'instructions': instructions,
            'cost': toll_cost,
            'toll_count': len(toll_details),
            'tolls': toll_details,
            'segments': {'count': 1, 'toll_segments': 1, 'free_segments': 0},
            'toll_info': {
                'selected_tolls': [t.get('name', 'Péage') for t in toll_details],
                'toll_systems': [],
                'coordinates': []
            }
        }
