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
                return {
                    'route': toll_free_route,
                    'status': 'no_toll_success',
                    'target_tolls': 0,
                    'strategy': 'toll_free_direct',
                    'distance': RouteUtils.extract_distance(toll_free_route),
                    'duration': RouteUtils.extract_duration(toll_free_route)
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
            'status': 'base_route_fallback',
            'target_tolls': None,  # Pas respecté, on retourne la route principale
            'strategy': 'base_route_return',
            'distance': RouteUtils.extract_distance(base_route),
            'duration': RouteUtils.extract_duration(base_route),
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
            'duration': duration1 + duration2
        }
