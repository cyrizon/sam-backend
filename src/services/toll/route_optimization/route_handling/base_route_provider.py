"""
Base Route Provider
==================

Fournit les routes de base pour l'optimisation.
Gère les étapes 1 et 2 : route sans péage et route avec tollways.
"""

from typing import List, Dict, Optional, Tuple
from ..utils.route_extractor import RouteExtractor
from .tollway_processor import TollwayProcessor


class BaseRouteProvider:
    """Fournisseur de routes de base."""
    
    def __init__(self, ors_service):
        """
        Initialise le fournisseur de routes.
        
        Args:
            ors_service: Service ORS pour les calculs de routes
        """
        self.ors = ors_service
        self.tollway_processor = TollwayProcessor()
    
    def get_toll_free_route(self, coordinates: List[List[float]]) -> Optional[Dict]:
        """
        ÉTAPE 1: Obtient une route sans péages.
        
        Args:
            coordinates: [départ, arrivée]
            
        Returns:
            Route sans péages formatée pour l'optimiseur
        """
        print("🚫 Étape 1: Récupération route sans péages...")
        
        try:
            # Utiliser la méthode ORS pour éviter les péages
            toll_free_route = self.ors.get_route_avoid_tollways(coordinates)
            
            if not toll_free_route:
                print("❌ Impossible d'obtenir une route sans péages")
                return None
            
            # Extraire les données de base
            route_coords = RouteExtractor.extract_coordinates(toll_free_route)
            distance = RouteExtractor.extract_distance(toll_free_route)
            duration = RouteExtractor.extract_duration(toll_free_route)
            instructions = RouteExtractor.extract_instructions(toll_free_route)
            
            print(f"✅ Route sans péages : {distance/1000:.1f}km, {duration/60:.1f}min")
            
            # Calculer les coûts de péages (devrait être 0)
            toll_cost, toll_details = self._calculate_toll_costs(toll_free_route)
            
            return {
                'route': toll_free_route,
                'route_coords': route_coords,
                'distance': distance,
                'duration': duration,
                'instructions': instructions,
                'toll_cost': toll_cost,
                'toll_details': toll_details,
                'strategy': 'toll_free',
                'segments_count': 1
            }
            
        except Exception as e:
            print(f"❌ Erreur route sans péages : {e}")
            return None
    
    def get_base_route_with_tollways(
        self, 
        coordinates: List[List[float]]
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        ÉTAPE 2: Obtient la route de base avec les segments tollways.
        
        Args:
            coordinates: [départ, arrivée]
            
        Returns:
            Tuple[route_data, tollways_data] : Route et segments tollways
        """
        print("🛣️ Étape 2: Route de base + segments tollways...")
        
        try:
            # Obtenir la route de base avec tollways
            base_route = self.ors.get_base_route(coordinates, include_tollways=True)
            
            if not base_route or "features" not in base_route:
                print("❌ Échec obtention route de base")
                return None, None
            
            # Extraire les données de base
            route_coords = RouteExtractor.extract_coordinates(base_route)
            distance = RouteExtractor.extract_distance(base_route)
            duration = RouteExtractor.extract_duration(base_route)
            instructions = RouteExtractor.extract_instructions(base_route)
            
            # Extraire les segments tollways
            tollways_data = RouteExtractor.extract_tollways_data(base_route)
            
            if not tollways_data:
                print("⚠️ Aucun segment tollway trouvé")
                tollways_data = {'segments': []}
            else:
                # Fusionner les petits segments tollways
                original_segments = tollways_data['segments']
                merged_segments = self.tollway_processor.merge_small_segments(
                    original_segments, min_waypoints=50
                )
                
                # Valider les segments
                if not self.tollway_processor.validate_segments(merged_segments):
                    print("⚠️ Segments invalides, utilisation des segments originaux")
                    merged_segments = original_segments
                
                tollways_data['segments'] = merged_segments
                
                # Mettre à jour les statistiques
                stats = self.tollway_processor.analyze_segments(merged_segments)
                tollways_data.update(stats)
            
            print(f"✅ Route de base : {distance/1000:.1f}km, {duration/60:.1f}min")
            print(f"   📊 Segments tollways : {len(tollways_data['segments'])}")
            
            route_data = {
                'route': base_route,
                'route_coords': route_coords,
                'distance': distance,
                'duration': duration,
                'instructions': instructions,
                'strategy': 'base_with_tollways'
            }
            
            return route_data, tollways_data
            
        except Exception as e:
            print(f"❌ Erreur route de base : {e}")
            return None, None
    
    def _calculate_toll_costs(self, route: Dict) -> Tuple[float, List[Dict]]:
        """
        Calcule les coûts de péages pour une route.
        
        Args:
            route: Route au format GeoJSON
            
        Returns:
            Tuple[coût_total, détails_péages]
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
    
    def validate_coordinates(self, coordinates: List[List[float]]) -> bool:
        """
        Valide les coordonnées d'entrée.
        
        Args:
            coordinates: Liste des coordonnées [départ, arrivée]
            
        Returns:
            True si valides, False sinon
        """
        if not coordinates or len(coordinates) < 2:
            print("❌ Coordonnées insuffisantes (minimum 2 points)")
            return False
        
        for i, coord in enumerate(coordinates):
            if not coord or len(coord) < 2:
                print(f"❌ Coordonnée {i} invalide")
                return False
            
            lon, lat = coord[0], coord[1]
            
            # Vérifier les limites géographiques
            if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
                print(f"❌ Coordonnée {i} hors limites : [{lon}, {lat}]")
                return False
        
        return True
