"""
no_toll_strategy.py
------------------

Stratégie pour calculer des itinéraires sans péage.
Responsabilité unique : éviter complètement les péages.
"""

from src.services.toll_locator import locate_tolls
from src.services.toll_cost import add_marginal_cost
from src.utils.route_utils import format_route_result
from benchmark.performance_tracker import performance_tracker


class NoTollStrategy:
    """
    Stratégie pour calculer des itinéraires sans péage.
    """
    
    def __init__(self, ors_service):
        """
        Initialise la stratégie avec un service ORS.
        
        Args:
            ors_service: Instance de ORSService pour les appels API
        """
        self.ors = ors_service
    
    def compute_route_no_toll(self, coordinates, veh_class="c1"):
        """
        Calcule un itinéraire sans péage en utilisant l'option avoid_features.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            veh_class: Classe de véhicule pour le calcul des coûts
            
        Returns:
            tuple: (route_data, status_code)
        """
        with performance_tracker.measure_operation("compute_route_no_toll"):
            print("Recherche d'un itinéraire sans péage...")
            
            try:
                with performance_tracker.measure_operation("ORS_avoid_tollways"):
                    performance_tracker.count_api_call("ORS_avoid_tollways")
                    toll_free_route = self.ors.get_route_avoid_tollways(coordinates)
                
                # Vérification qu'il n'y a vraiment pas de péage
                with performance_tracker.measure_operation("locate_tolls_no_toll"):
                    tolls_on_route = locate_tolls(toll_free_route, "data/barriers.csv")["on_route"]
                
                if tolls_on_route:
                    print(f"Attention: l'itinéraire sans péage contient quand même {len(tolls_on_route)} péages")
                    add_marginal_cost(tolls_on_route, veh_class)
                    cost = sum(t.get("cost", 0) for t in tolls_on_route)
                    
                    return format_route_result(
                        toll_free_route,
                        cost,
                        toll_free_route["features"][0]["properties"]["summary"]["duration"],
                        len(tolls_on_route)
                    ), "SOME_TOLLS_PRESENT"
                else:
                    return format_route_result(
                        toll_free_route,
                        0,
                        toll_free_route["features"][0]["properties"]["summary"]["duration"],
                        0
                    ), "NO_TOLL_SUCCESS"
            
            except Exception as e:
                performance_tracker.log_error(f"Impossible de trouver un itinéraire sans péage: {e}")
                print(f"Impossible de trouver un itinéraire sans péage: {e}")
                return None, "NO_TOLL_ROUTE_NOT_POSSIBLE"
    
    def handle_no_toll_route(self, coordinates, veh_class="c1"):
        """
        Gère le cas où aucun péage n'est autorisé.
        Point d'entrée principal pour les routes sans péage.
        
        Returns:
            dict: Résultat formaté avec fastest, cheapest, min_tolls, status
        """
        with performance_tracker.measure_operation("handle_no_toll_route"):
            no_toll_result, status = self.compute_route_no_toll(coordinates, veh_class)
            
            if no_toll_result:
                return {
                    "fastest": no_toll_result,
                    "cheapest": no_toll_result,
                    "min_tolls": no_toll_result,
                    "status": status
                }
            else:
                # Import ici pour éviter les imports circulaires
                from src.services.toll.fallback_strategy import FallbackStrategy
                fallback = FallbackStrategy(self.ors)
                return fallback.get_fallback_route(coordinates, veh_class, status)