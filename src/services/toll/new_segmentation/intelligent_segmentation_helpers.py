"""
intelligent_segmentation_helpers.py
----------------------------------

Classes d'aide pour la segmentation intelligente.
Gère les cas spéciaux et les utilitaires pour éviter que le fichier principal dépasse 350 lignes.
"""

import os
from typing import List, Dict, Optional


class SegmentationSpecialCases:
    """
    Gère les cas spéciaux de la segmentation intelligente.
    """
    
    def __init__(self, ors_service):
        """
        Initialise avec le service ORS.
        
        Args:
            ors_service: Service ORS pour les calculs de routes
        """
        self.ors = ors_service
    
    def get_toll_free_route(self, coordinates: List[List[float]]) -> Optional[Dict]:
        """
        Cas spécial : Obtient une route sans péages (évitement total des péages).
        Reproduit la logique de la stratégie simple pour le cas 0 péage.
        
        Args:
            coordinates: [départ, arrivée]
              Returns:
            dict: Route sans péages ou None si échec
        """
        try:
            print("🚫 Récupération de la route sans péages...")
            
            # Utiliser la méthode spécifique ORS pour éviter les péages
            toll_free_route = self.ors.get_route_avoid_tollways(coordinates)
            if toll_free_route:
                print("✅ Route sans péages trouvée avec get_route_avoid_tollways")
                
                # Extraire les instructions et les ajouter au GeoJSON si elles ne sont pas déjà présentes
                instructions = RouteUtils.extract_instructions(toll_free_route)
                  # S'assurer que les instructions sont dans le GeoJSON
                if 'features' in toll_free_route and toll_free_route['features']:
                    feature = toll_free_route['features'][0]
                    if 'properties' not in feature:
                        feature['properties'] = {}
                    if 'instructions' not in feature['properties'] and instructions:
                        feature['properties']['instructions'] = instructions
                
                # Calculer les informations de péages (comme dans /api/route/)
                detailed_tolls = []
                total_toll_cost = 0
                try:
                    from src.services.toll_locator import locate_tolls
                    from src.services.toll_cost import add_marginal_cost
                    
                    tolls_dict = locate_tolls(toll_free_route, buffer_m=1.0, veh_class="c1")
                    detailed_tolls = add_marginal_cost(tolls_dict["on_route"], veh_class="c1")
                    total_toll_cost = sum(t.get("cost", 0) for t in detailed_tolls)
                    
                    print(f"💰 Route sans péages - Coût : {total_toll_cost}€ (devrait être 0)")
                    
                except Exception as e:
                    print(f"⚠️ Erreur calcul coût route sans péages : {e}")
                    detailed_tolls = []
                    total_toll_cost = 0                
                return {
                    'route': toll_free_route,
                    'target_tolls': 0,
                    'found_solution': 'no_toll_success',
                    'respects_constraint': True,
                    'strategy_used': 'toll_free_direct',
                    'distance': RouteUtils.extract_distance(toll_free_route),
                    'duration': RouteUtils.extract_duration(toll_free_route),
                    'instructions': instructions,
                    'cost': total_toll_cost,  # Coût total des péages (devrait être 0)
                    'toll_count': len(detailed_tolls),  # Nombre de péages (devrait être 0)
                    'tolls': detailed_tolls,  # Détails des péages (devrait être [])
                    'segments': {'count': 1, 'toll_segments': 0, 'free_segments': 1},
                    'toll_info': {
                        'selected_tolls': [],
                        'toll_systems': [],
                        'coordinates': []
                    }
                }
            else:
                print("❌ Impossible de trouver une route sans péages")
                return None
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération de la route sans péages : {e}")
            return None
    
    def format_base_route_as_result(self, base_route: Dict, target_tolls: int = None) -> Dict:
        """
        Cas spécial : Formate la route de base comme résultat final.
        Utilisé quand l'utilisateur demande plus de péages qu'il n'y en a sur la route.
        
        Args:
            base_route: Route de base ORS
            target_tolls: Nombre de péages demandés (pour homogénéité de la réponse)
            
        Returns:
            dict: Route de base formatée
        """
        print("🔄 Formatage de la route de base comme résultat final")
        
        # Récupérer une route complète avec instructions
        # Extraire les coordonnées de départ et d'arrivée
        try:
            coordinates = RouteUtils.extract_route_coordinates(base_route)
            if coordinates and len(coordinates) >= 2:
                start_coord = coordinates[0]
                end_coord = coordinates[-1]
                print(f"🗺️ Récupération des instructions pour {start_coord} → {end_coord}")
                
                # Récupérer une route complète avec instructions
                full_route = self.ors.get_route(start_coord, end_coord)
                if full_route:
                    print("✅ Route complète avec instructions récupérée")
                    instructions = RouteUtils.extract_instructions(full_route)
                    print(f"📝 {len(instructions)} instructions trouvées")
                else:
                    print("⚠️ Impossible de récupérer la route complète, utilisation de la route de base")
                    instructions = RouteUtils.extract_instructions(base_route)
            else:
                print("⚠️ Impossible d'extraire les coordonnées, utilisation de la route de base")
                instructions = RouteUtils.extract_instructions(base_route)
        except Exception as e:
            print(f"⚠️ Erreur lors de la récupération des instructions : {e}")
            instructions = RouteUtils.extract_instructions(base_route)
        
        # Calculer les informations de péages (comme dans /api/route/)
        detailed_tolls = []
        total_toll_cost = 0
        try:
            from src.services.toll_locator import locate_tolls
            from src.services.toll_cost import add_marginal_cost
            
            tolls_dict = locate_tolls(base_route, buffer_m=1.0, veh_class="c1")
            detailed_tolls = add_marginal_cost(tolls_dict["on_route"], veh_class="c1")
            total_toll_cost = sum(t.get("cost", 0) for t in detailed_tolls)
            
            print(f"💰 Route de base - Coût : {total_toll_cost}€")
            print(f"🏧 Route de base - Péages : {len(detailed_tolls)} trouvés")
        except Exception as e:
            print(f"⚠️ Erreur calcul coût route de base : {e}")
            detailed_tolls = []
            total_toll_cost = 0
        # Nettoyer les duplications dans le GeoJSON
        from .response_harmonizer import ResponseHarmonizer
        cleaned_route = ResponseHarmonizer.clean_geojson_duplications(base_route)
          # Construire les toll_info à partir des péages détectés
        toll_info = {
            'selected_tolls': [toll.get('name', toll.get('id', '')) for toll in detailed_tolls],
            'toll_systems': [
                "ouvert" if toll.get('role') == 'O' else "fermé" 
                for toll in detailed_tolls
            ],
            'coordinates': [
                {
                    'name': toll.get('name', toll.get('id', '')),
                    'lat': toll.get('latitude', 0),
                    'lon': toll.get('longitude', 0)
                }
                for toll in detailed_tolls
            ]
        }
          # Calculer les segments correctement pour une route de base
        # Une route de base = 1 segment principal qui traverse des péages
        # Pas de segmentation réelle, juste identification des péages traversés
        toll_segments_count = len(detailed_tolls)
        
        return {
            'route': cleaned_route,  # Route nettoyée sans duplications
            'target_tolls': target_tolls,  # Toujours égal à la demande utilisateur
            'found_solution': 'base_route_fallback',
            'respects_constraint': False,
            'strategy_used': 'base_route_return',
            'distance': RouteUtils.extract_distance(base_route),
            'duration': RouteUtils.extract_duration(base_route),
            'instructions': instructions,  # Utiliser les instructions récupérées
            'cost': total_toll_cost,  # Coût total des péages
            'toll_count': len(detailed_tolls),  # Nombre de péages
            'tolls': detailed_tolls,  # Détails des péages
            'segments': {
                'count': 1,  # Une seule route (pas de segmentation)
                'toll_segments': toll_segments_count,  # Nombre de péages sur cette route
                'free_segments': 0   # Pas de segments sans péages (route continue avec péages)
            },
            'toll_info': toll_info,
            'note': 'Plus de péages demandés que disponibles, route principale retournée'
        }


class RouteUtils:
    """
    Utilitaires pour l'extraction de données des routes.
    """
    
    @staticmethod
    def extract_distance(route: Dict) -> float:
        """Extrait la distance d'une route ORS."""
        try:
            # Handle new hybrid segment format
            if 'route' in route and 'segment_info' in route:
                # New format: extract from route sub-dict
                return route['route']['features'][0]['properties']['summary']['distance']
            else:
                # Legacy format: direct access
                return route['features'][0]['properties']['summary']['distance']
        except (KeyError, IndexError):
            return 0.0
    
    @staticmethod
    def extract_duration(route: Dict) -> float:
        """Extrait la durée d'une route ORS."""
        try:
            # Handle new hybrid segment format
            if 'route' in route and 'segment_info' in route:
                # New format: extract from route sub-dict
                return route['route']['features'][0]['properties']['summary']['duration']
            else:
                # Legacy format: direct access
                return route['features'][0]['properties']['summary']['duration']
        except (KeyError, IndexError):
            return 0.0
    
    @staticmethod
    def extract_route_coordinates(route: Dict) -> List[List[float]]:
        """Extrait les coordonnées de la route."""
        try:
            # Handle new hybrid segment format
            if 'route' in route and 'segment_info' in route:
                # New format: extract from route sub-dict
                return route['route']['features'][0]['geometry']['coordinates']
            else:
                # Legacy format: direct access
                return route['features'][0]['geometry']['coordinates']
        except (KeyError, IndexError):
            return []
    
    @staticmethod
    def extract_instructions(route: Dict) -> List[Dict]:
        """Extrait les instructions de navigation d'une route ORS."""
        try:
            # Handle new hybrid segment format
            if 'route' in route and 'segment_info' in route:
                # New format: extract from route sub-dict
                actual_route = route['route']
            else:
                # Legacy format: direct access
                actual_route = route
            
            # Debug : afficher la structure de la route
            if 'features' in actual_route and actual_route['features']:
                feature = actual_route['features'][0]
                properties = feature.get('properties', {})
                print(f"🔍 Debug instructions - properties keys: {list(properties.keys())}")
                
                if 'segments' in properties:
                    segments = properties['segments']
                    print(f"🔍 Debug instructions - segments count: {len(segments)}")
                    if segments:
                        first_segment = segments[0]
                        print(f"🔍 Debug instructions - first segment keys: {list(first_segment.keys())}")
                else:
                    print("🔍 Debug instructions - no 'segments' in properties")
            
            segments = actual_route['features'][0]['properties']['segments']
            if not segments:
                return []
            
            instructions = []
            for segment in segments:
                steps = segment.get('steps', [])
                for step in steps:
                    instructions.append({
                        'instruction': step.get('instruction', ''),
                        'distance': step.get('distance', 0),
                        'duration': step.get('duration', 0),
                        'type': step.get('type', 0),
                        'name': step.get('name', ''),
                        'way_points': step.get('way_points', [])
                    })
            return instructions
        except (KeyError, IndexError) as e:
            print(f"🔍 Debug instructions - Error: {e}")
            return []


class RouteAssembler:
    """
    Gère l'assemblage des routes segmentées.
    """
    
    @staticmethod
    def assemble_final_route(segment1: Dict, segment2: Dict, target_tolls: int) -> Dict:
        """
        Étape 8-9 : Assemble la route finale à partir des deux segments.
        
        Args:
            segment1: Premier segment (avec péages)
            segment2: Deuxième segment (sans péages)  
            target_tolls: Nombre de péages ciblé
            
        Returns:
            dict: Route finale assemblée
        """
        print("🔧 Étapes 8-9 : Assemblage de la route finale...")
        
        # Extraire les coordonnées des deux segments
        coords1 = RouteUtils.extract_route_coordinates(segment1)
        coords2 = RouteUtils.extract_route_coordinates(segment2)
        
        if not coords1 or not coords2:
            print("❌ Impossible d'extraire les coordonnées des segments")
            return None
        
        # Fusionner en évitant la duplication du point de jonction
        final_coords = coords1 + coords2[1:]  # Enlever le premier point du segment 2
          # Calculer les métriques totales
        distance1 = RouteUtils.extract_distance(segment1)
        distance2 = RouteUtils.extract_distance(segment2)
        duration1 = RouteUtils.extract_duration(segment1)
        duration2 = RouteUtils.extract_duration(segment2)
        
        # Extraire et assembler les instructions
        instructions1 = RouteUtils.extract_instructions(segment1)
        instructions2 = RouteUtils.extract_instructions(segment2)
        final_instructions = instructions1 + instructions2
        
        # Créer la route finale au format GeoJSON
        final_route = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": final_coords
                },
                "properties": {
                    "summary": {
                        "distance": distance1 + distance2,
                        "duration": duration1 + duration2
                    },
                    "segments": [
                        segment1['features'][0]['properties'],
                        segment2['features'][0]['properties']
                    ]
                }
            }]
        }
        print(f"✅ Route assemblée : {(distance1 + distance2)/1000:.1f} km, {(duration1 + duration2)/60:.0f} min")
        
        return {
            'route': final_route,
            'status': 'intelligent_segmentation_success',
            'target_tolls': target_tolls,
            'strategy': 'intelligent_segmentation',
            'segments': {
                'segment1': segment1,
                'segment2': segment2
            },
            'distance': distance1 + distance2,
            'duration': duration1 + duration2,
            'instructions': final_instructions
        }
