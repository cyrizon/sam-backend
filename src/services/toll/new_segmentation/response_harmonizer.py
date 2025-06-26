"""
Module pour harmoniser les réponses des différentes stratégies.
Responsabilité : Nettoyer les GeoJSON et standardiser les formats de réponse.
"""

from typing import Dict, List, Optional
import os


class ResponseHarmonizer:
    """
    Harmonise les réponses des différentes stratégies pour avoir un format uniforme.
    """
    
    @staticmethod
    def clean_geojson_duplications(route: Dict) -> Dict:
        """
        Nettoie les duplications dans le GeoJSON (instructions, segments steps).
        
        Args:
            route: Route GeoJSON à nettoyer
            
        Returns:
            dict: Route nettoyée sans duplications
        """
        if not route or 'features' not in route:
            return route
            
        try:
            # Copier la route pour ne pas modifier l'original
            clean_route = route.copy()
            
            # Nettoyer chaque feature
            for feature in clean_route.get('features', []):
                if 'properties' not in feature:
                    continue
                    
                properties = feature['properties']
                
                # Supprimer les instructions dupliquées des properties
                if 'instructions' in properties:
                    del properties['instructions']
                
                # Nettoyer les segments (supprimer les steps qui sont dupliqués)
                if 'segments' in properties:
                    for segment in properties['segments']:
                        if isinstance(segment, dict) and 'steps' in segment:
                            del segment['steps']
            return clean_route
            
        except Exception as e:
            print(f"⚠️ Erreur nettoyage GeoJSON : {e}")
            return route
    
    @staticmethod
    def calculate_toll_info(route: Dict, veh_class: str = "c1") -> tuple:
        """
        Calcule les informations de péages pour une route.
        
        Args:
            route: Route GeoJSON
            veh_class: Classe de véhicule
            
        Returns:
            tuple: (detailed_tolls, total_cost)
        """
        detailed_tolls = []
        total_toll_cost = 0
        
        # Vérifier que la route a une géométrie valide
        if not route or not isinstance(route, dict):
            return detailed_tolls, total_toll_cost
            
        if 'features' not in route or not route['features']:
            return detailed_tolls, total_toll_cost
            
        if 'geometry' not in route['features'][0]:
            return detailed_tolls, total_toll_cost
        
        try:
            from src.services.toll_locator import locate_tolls
            from src.services.toll_cost import add_marginal_cost
            
            tolls_dict = locate_tolls(route, buffer_m=1.0, veh_class="c1")
            detailed_tolls = add_marginal_cost(tolls_dict["on_route"], veh_class=veh_class)
            total_toll_cost = sum(t.get("cost", 0) for t in detailed_tolls)
            
        except Exception as e:
            print(f"⚠️ Erreur calcul coût péages : {e}")
            detailed_tolls = []
            total_toll_cost = 0
            
        return detailed_tolls, total_toll_cost
    
    @staticmethod
    def create_standard_response(
        route: Dict,
        instructions: Optional[List] = None,
        detailed_tolls: Optional[List] = None,
        total_cost: float = 0,
        target_tolls: Optional[int] = None,
        found_solution: str = "success",
        strategy_used: str = "unknown",
        respects_constraint: bool = True,
        segments_info: Optional[Dict] = None,
        **extra_props
    ) -> Dict:
        """
        Crée une réponse standardisée avec toutes les propriétés harmonisées.
        
        Args:
            route: Route GeoJSON
            instructions: Instructions de navigation
            detailed_tolls: Détails des péages
            total_cost: Coût total des péages
            target_tolls: Nombre de péages ciblé
            found_solution: Type de solution trouvée
            strategy_used: Stratégie utilisée
            respects_constraint: Si la contrainte est respectée
            segments_info: Informations sur les segments
            **extra_props: Propriétés supplémentaires spécifiques
            
        Returns:
            dict: Réponse harmonisée
        """
        from src.services.toll.new_segmentation.intelligent_segmentation_helpers import RouteUtils
        
        # Nettoyer le GeoJSON
        clean_route = ResponseHarmonizer.clean_geojson_duplications(route)
        
        # Extraire les propriétés de base
        distance = RouteUtils.extract_distance(route)
        duration = RouteUtils.extract_duration(route)
        
        # Utiliser les instructions fournies ou les extraire
        if instructions is None:
            instructions = RouteUtils.extract_instructions(route)
        
        # Utiliser les péages fournis ou calculer
        if detailed_tolls is None:
            detailed_tolls, total_cost = ResponseHarmonizer.calculate_toll_info(route)
        
        # Segments par défaut
        if segments_info is None:
            segments_info = {"count": 1, "toll_segments": 1 if detailed_tolls else 0, "free_segments": 1}
        
        # Créer toll_info standardisé
        toll_info = {
            "selected_tolls": [t.get('name', t.get('id', '')) for t in detailed_tolls],
            "toll_systems": [],  # À remplir selon la stratégie
            "coordinates": [
                {"name": t.get('name', t.get('id', '')), "lat": t.get('latitude', 0), "lon": t.get('longitude', 0)}
                for t in detailed_tolls
            ]
        }
        
        # Réponse standardisée
        response = {
            # Propriétés principales pour le frontend
            'route': clean_route,
            'target_tolls': target_tolls,
            'found_solution': found_solution,
            'respects_constraint': respects_constraint,
            'strategy_used': strategy_used,
            'distance': distance,
            'duration': duration,
            'instructions': instructions,
            'cost': total_cost,
            'toll_count': len(detailed_tolls),
            'tolls': detailed_tolls,
            'segments': segments_info,
            'toll_info': toll_info
        }
        
        # Ajouter les propriétés supplémentaires (sans écraser les principales)
        for key, value in extra_props.items():
            if key not in response:
                response[key] = value
        
        return response
