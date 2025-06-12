"""
route_tester.py
--------------

Classe responsable des tests et validations de routes pour les stratégies de péages.
Centralise la logique de test des routes alternatives et de validation des contraintes.
"""

from src.services.toll.route_calculator import RouteCalculator
from src.services.common.result_formatter import ResultFormatter


class RouteTester:
    """
    Testeur et validateur de routes pour les stratégies de péages.
    """
    
    def __init__(self, ors_service):
        self.route_calculator = RouteCalculator(ors_service)
    
    def test_base_route(self, coordinates, target_tolls, veh_class, exact_match=False):
        """
        Teste la route directe.
        
        Args:
            coordinates: Coordonnées de départ et arrivée
            target_tolls: Nombre de péages cible
            veh_class: Classe de véhicule
            exact_match: Si True, vérifie l'égalité exacte, sinon ≤
            
        Returns:
            dict: Route formatée si valide, None sinon
        """
        try:
            base_route = self.route_calculator.get_base_route_with_tracking(coordinates)
            
            tolls_dict = self.route_calculator.locate_and_cost_tolls(
                base_route, veh_class, f"locate_tolls_base_{'exact' if exact_match else 'limit'}_{target_tolls}"
            )
            tolls_on_route = tolls_dict["on_route"]
            toll_count = len(tolls_on_route)
            
            print(f"Route directe: {toll_count} péages (cible: {target_tolls})")
            
            # Vérifier la condition
            is_valid = toll_count == target_tolls if exact_match else toll_count <= target_tolls
            
            if is_valid:
                cost = sum(t.get("cost", 0) for t in tolls_on_route)
                duration = base_route["features"][0]["properties"]["summary"]["duration"]
                
                return ResultFormatter.format_route_result(
                    base_route, cost, duration, toll_count
                )
            
            return None
            
        except Exception as e:
            print(f"❌ Erreur route directe: {e}")
            return None
    
    def test_avoiding_route(self, coordinates, target_tolls, veh_class, exact_match=False):
        """
        Teste la route avec évitement des péages.
        
        Args:
            coordinates: Coordonnées de départ et arrivée
            target_tolls: Nombre de péages cible
            veh_class: Classe de véhicule
            exact_match: Si True, vérifie l'égalité exacte, sinon ≤
            
        Returns:
            dict: Route formatée si valide, None sinon
        """
        try:
            avoiding_route = self.route_calculator.get_route_avoid_tollways_with_tracking(coordinates)
            
            tolls_dict = self.route_calculator.locate_and_cost_tolls(
                avoiding_route, veh_class, f"locate_tolls_avoiding_{'exact' if exact_match else 'limit'}_{target_tolls}"
            )
            tolls_on_route = tolls_dict["on_route"]
            toll_count = len(tolls_on_route)
            
            print(f"Route évitement: {toll_count} péages (cible: {target_tolls})")
            
            # Vérifier la condition
            is_valid = toll_count == target_tolls if exact_match else toll_count <= target_tolls
            
            if is_valid:
                cost = sum(t.get("cost", 0) for t in tolls_on_route)
                duration = avoiding_route["features"][0]["properties"]["summary"]["duration"]
                
                return ResultFormatter.format_route_result(
                    avoiding_route, cost, duration, toll_count
                )
            
            return None
            
        except Exception as e:
            print(f"❌ Erreur route évitement: {e}")
            return None
    
    def test_toll_avoidance_with_polygon(self, tolls_to_avoid_list, coordinates, target_tolls, veh_class, radius_m, exact_match=False):
        """
        Teste l'évitement d'une liste de péages avec un polygone d'évitement.
        
        Args:
            tolls_to_avoid_list: Liste des péages à éviter
            coordinates: Coordonnées de départ et arrivée
            target_tolls: Nombre de péages cible
            veh_class: Classe de véhicule
            radius_m: Rayon du polygone d'évitement en mètres
            exact_match: Si True, vérifie l'égalité exacte, sinon ≤
            
        Returns:
            dict: Route formatée si valide, None sinon
        """
        try:
            print(f"   Test évitement de {len(tolls_to_avoid_list)} péages (rayon {radius_m}m)")
            
            # Préparer les données pour poly_utils
            tolls_for_avoidance = []
            for toll in tolls_to_avoid_list:
                tolls_for_avoidance.append({
                    "longitude": toll.get("lon", toll.get("longitude")),
                    "latitude": toll.get("lat", toll.get("latitude"))
                })
            
            if not tolls_for_avoidance:
                return None
            
            # Créer le multipolygon d'évitement
            from src.utils.poly_utils import avoidance_multipolygon
            avoid_poly = avoidance_multipolygon(tolls_for_avoidance, radius_m=radius_m)
            
            # Calculer route alternative
            alternative_route = self.route_calculator.get_route_avoiding_polygons_with_tracking(
                coordinates, avoid_poly
            )
            
            if alternative_route:
                # Analyser les péages de la route alternative
                alt_tolls_dict = self.route_calculator.locate_and_cost_tolls(
                    alternative_route, veh_class, f"locate_tolls_avoid_test_{'exact' if exact_match else 'limit'}"
                )
                alt_tolls_on_route = alt_tolls_dict["on_route"]
                alt_toll_count = len(alt_tolls_on_route)
                
                print(f"   Route alternative: {alt_toll_count} péages")
                
                # Vérifier la condition
                is_valid = alt_toll_count == target_tolls if exact_match else alt_toll_count <= target_tolls
                
                if is_valid:
                    cost = sum(t.get("cost", 0) for t in alt_tolls_on_route)
                    duration = alternative_route["features"][0]["properties"]["summary"]["duration"]
                    
                    return ResultFormatter.format_route_result(
                        alternative_route, cost, duration, alt_toll_count
                    )
                elif exact_match and alt_toll_count <= target_tolls + 2:
                    # Pour la recherche exacte, retourner quand même si proche
                    cost = sum(t.get("cost", 0) for t in alt_tolls_on_route)
                    duration = alternative_route["features"][0]["properties"]["summary"]["duration"]
                    
                    return ResultFormatter.format_route_result(
                        alternative_route, cost, duration, alt_toll_count
                    )
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ Erreur test évitement: {e}")
            return None
    
    def get_base_route_tolls(self, coordinates, veh_class):
        """
        Récupère les péages de la route de base pour analyse.
        
        Returns:
            tuple: (route, tolls_on_route, toll_count) ou (None, None, 0) en cas d'erreur
        """
        try:
            base_route = self.route_calculator.get_base_route_with_tracking(coordinates)
            tolls_dict = self.route_calculator.locate_and_cost_tolls(
                base_route, veh_class, "locate_tolls_analysis"
            )
            tolls_on_route = tolls_dict["on_route"]
            toll_count = len(tolls_on_route)
            
            return base_route, tolls_on_route, toll_count
            
        except Exception as e:
            print(f"❌ Erreur analyse route de base: {e}")
            return None, None, 0
