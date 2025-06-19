"""
intelligent_segmentation_helpers.py
----------------------------------

Classes d'aide pour la segmentation intelligente.
Gère les cas spéciaux et les utilitaires pour éviter que le fichier principal dépasse 350 lignes.
"""

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
                return {
                    'route': toll_free_route,
                    'target_tolls': 0,
                    'found_solution': 'no_toll_success',
                    'respects_constraint': True,
                    'strategy_used': 'toll_free_direct',
                    'distance': RouteUtils.extract_distance(toll_free_route),
                    'duration': RouteUtils.extract_duration(toll_free_route),
                    'instructions': instructions,
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
    
    def format_base_route_as_result(self, base_route: Dict) -> Dict:
        """
        Cas spécial : Formate la route de base comme résultat final.
        Utilisé quand l'utilisateur demande plus de péages qu'il n'y en a sur la route.
        
        Args:
            base_route: Route de base ORS
            
        Returns:
            dict: Route de base formatée
        """
        print("🔄 Formatage de la route de base comme résultat final")        
        return {
            'route': base_route,
            'target_tolls': None,  # Pas respecté, on retourne la route principale
            'found_solution': 'base_route_fallback',
            'respects_constraint': False,
            'strategy_used': 'base_route_return',
            'distance': RouteUtils.extract_distance(base_route),
            'duration': RouteUtils.extract_duration(base_route),
            'instructions': RouteUtils.extract_instructions(base_route),
            'segments': {'count': 1, 'toll_segments': 0, 'free_segments': 1},
            'toll_info': {
                'selected_tolls': [],
                'toll_systems': [],
                'coordinates': []
            },
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
            return route['features'][0]['properties']['summary']['distance']
        except (KeyError, IndexError):
            return 0.0
    
    @staticmethod
    def extract_duration(route: Dict) -> float:
        """Extrait la durée d'une route ORS."""
        try:
            return route['features'][0]['properties']['summary']['duration']
        except (KeyError, IndexError):
            return 0.0
    
    @staticmethod
    def extract_route_coordinates(route: Dict) -> List[List[float]]:
        """Extrait les coordonnées de la route."""
        try:
            return route['features'][0]['geometry']['coordinates']
        except (KeyError, IndexError):
            return []
    
    @staticmethod
    def extract_instructions(route: Dict) -> List[Dict]:
        """Extrait les instructions de navigation d'une route ORS."""
        try:
            segments = route['features'][0]['properties']['segments']
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
        except (KeyError, IndexError):
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
