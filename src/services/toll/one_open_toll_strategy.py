"""
one_open_toll_strategy.py
------------------------

Stratégie pour calculer des itinéraires passant par exactement un péage à système ouvert.
Responsabilité unique : optimiser les routes avec un seul péage ouvert.
"""

from src.services.toll_locator import locate_tolls, get_all_open_tolls_by_proximity
from src.services.toll_cost import add_marginal_cost
from src.utils.poly_utils import avoidance_multipolygon
from src.utils.route_utils import is_toll_open_system, merge_routes, format_route_result
from benchmark.performance_tracker import performance_tracker


class OneOpenTollStrategy:
    """
    Stratégie pour calculer des itinéraires avec exactement un péage ouvert.
    """
    
    def __init__(self, ors_service):
        """
        Initialise la stratégie avec un service ORS.
        
        Args:
            ors_service: Instance de ORSService pour les appels API
        """
        self.ors = ors_service
    
    def compute_route_with_one_open_toll(self, coordinates, veh_class="c1"):
        """
        Calcule un itinéraire qui passe par exactement un péage à système ouvert.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            veh_class: Classe de véhicule pour le calcul des coûts
            
        Returns:
            tuple: (route_data, status_code)
        """
        with performance_tracker.measure_operation("compute_route_with_one_open_toll"):
            print("Recherche d'un itinéraire avec un seul péage ouvert...")
            
            # 1) Obtenir la route de base pour identifier les péages à proximité
            try:
                with performance_tracker.measure_operation("ORS_base_route_one_toll"):
                    performance_tracker.count_api_call("ORS_base_route")
                    base_route = self.ors.get_base_route(coordinates)
            except Exception as e:
                performance_tracker.log_error(f"Erreur lors de l'appel initial à ORS: {e}")
                print(f"Erreur lors de l'appel initial à ORS: {e}")
                return None, "ORS_CONNECTION_ERROR"
            
            # 2) Localiser tous les péages sur et à proximité de la route
            with performance_tracker.measure_operation("locate_tolls_one_toll"):
                tolls_dict = locate_tolls(base_route, "data/barriers.csv")
                tolls_on_route = tolls_dict["on_route"]
                tolls_nearby = tolls_dict["nearby"]
                local_tolls = tolls_on_route + tolls_nearby
            
            # 3) Filtrer pour ne garder que les péages à système ouvert à proximité
            with performance_tracker.measure_operation("filter_open_tolls"):
                nearby_open_tolls = [toll for toll in local_tolls if is_toll_open_system(toll["id"])]
            
            # Variables pour stocker la meilleure solution
            best_route = None
            best_cost = float('inf')
            best_duration = float('inf')
            best_toll_id = None
            min_toll_count = float('inf')
            min_toll_route = None
            min_toll_cost = float('inf')
            min_toll_duration = float('inf')
            min_toll_id = None
            
            print(f"Trouvé {len(nearby_open_tolls)} péages ouverts à proximité immédiate")
            
            # 4) Première étape: test avec les péages ouverts à proximité immédiate
            if nearby_open_tolls:
                with performance_tracker.measure_operation("test_nearby_open_tolls", {"count": len(nearby_open_tolls)}):
                    best_route, best_cost, best_duration, best_toll_id, min_toll_count, min_toll_route, min_toll_cost, min_toll_duration, min_toll_id = self._try_route_with_tolls(
                        coordinates, nearby_open_tolls, veh_class
                    )
            
            # 5) Si aucun résultat avec les péages proches, tester avec tous les péages ouverts du réseau
            if best_route is None:
                print("Aucune solution trouvée avec les péages ouverts à proximité. Test avec tous les péages ouverts du réseau...")
                
                # 5.1) Récupérer tous les péages ouverts triés par proximité avec la route
                # Limiter la recherche aux péages dans un rayon de 100 km
                max_distance_m = 100000  # 100 km
                with performance_tracker.measure_operation("get_all_open_tolls", {"max_distance_m": max_distance_m}):
                    all_open_tolls = get_all_open_tolls_by_proximity(base_route, "data/barriers.csv", max_distance_m)
                
                if not all_open_tolls:
                    print(f"Aucun péage à système ouvert trouvé dans un rayon de {max_distance_m/1000:.1f} km")
                    return None, "NO_OPEN_TOLL_FOUND"
                
                print(f"Trouvé {len(all_open_tolls)} péages ouverts dans un rayon de {max_distance_m/1000:.1f} km")
                
                # 5.2) Les tester dans l'ordre de proximité
                # On n'utilise que les 10 plus proches pour limiter le temps de calcul
                with performance_tracker.measure_operation("test_all_open_tolls", {"count": min(10, len(all_open_tolls))}):
                    best_route, best_cost, best_duration, best_toll_id, min_toll_count, min_toll_route, min_toll_cost, min_toll_duration, min_toll_id = self._try_route_with_tolls(
                        coordinates, all_open_tolls[:10], veh_class, best_route, best_cost, best_duration, best_toll_id, 
                        min_toll_count, min_toll_route, min_toll_cost, min_toll_duration, min_toll_id
                    )
            
            # 6) Résultat final
            if best_route:
                result = format_route_result(
                    best_route,
                    best_cost,
                    best_duration,
                    1,
                    best_toll_id
                )
                return result, "ONE_OPEN_TOLL_SUCCESS"
            elif min_toll_route:
                # Si on n'a pas trouvé de solution avec exactement un péage, on retourne la solution avec le minimum de péages
                print(f"Pas de solution trouvée avec exactement un péage ouvert, mais trouvé une solution avec {min_toll_count} péages")
                result = format_route_result(
                    min_toll_route,
                    min_toll_cost,
                    min_toll_duration,
                    min_toll_count,
                    min_toll_id
                )
                return result, "MINIMUM_TOLLS_SOLUTION"
            else:
                return None, "NO_VALID_OPEN_TOLL_ROUTE"
    
    def _try_route_with_tolls(
        self,
        coordinates, 
        tolls_to_try, 
        veh_class="c1",
        current_best_route=None,
        current_best_cost=float('inf'),
        current_best_duration=float('inf'),
        current_best_toll_id=None,
        current_min_toll_count=float('inf'),
        current_min_toll_route=None,
        current_min_toll_cost=float('inf'),
        current_min_toll_duration=float('inf'),
        current_min_toll_id=None
    ):
        """
        Fonction auxiliaire pour tester des itinéraires avec une liste de péages donnée.
        
        Returns:
            tuple: (best_route, best_cost, best_duration, best_toll_id, min_toll_count, min_toll_route, min_toll_cost, min_toll_duration, min_toll_id)
        """
        with performance_tracker.measure_operation("try_route_with_tolls", {"tolls_count": len(tolls_to_try)}):
            best_route = current_best_route
            best_cost = current_best_cost
            best_duration = current_best_duration
            best_toll_id = current_best_toll_id
            min_toll_count = current_min_toll_count
            min_toll_route = current_min_toll_route
            min_toll_cost = current_min_toll_cost
            min_toll_duration = current_min_toll_duration
            min_toll_id = current_min_toll_id
            
            for toll in tolls_to_try:
                with performance_tracker.measure_operation("test_single_toll", {"toll_id": toll["id"]}):
                    print(f"Test avec péage ouvert: {toll['id']}")
                    toll_coords = [toll["longitude"], toll["latitude"]]
                    
                    # 1) Partie 1: Départ → péage (d'abord sans restrictions)
                    part1_payload = {
                        "coordinates": [coordinates[0], toll_coords],
                        "extra_info": ["tollways"]
                    }
                    
                    try:
                        # D'abord on génère un itinéraire sans restrictions
                        with performance_tracker.measure_operation("ORS_part1_route"):
                            performance_tracker.count_api_call("ORS_alternative_route")
                            part1_route = self.ors.call_ors(part1_payload)
                        
                        # On vérifie quels péages sont sur cet itinéraire
                        with performance_tracker.measure_operation("locate_tolls_part1"):
                            part1_tolls = locate_tolls(part1_route, "data/barriers.csv")["on_route"]
                        
                        # Si le péage cible n'est pas le seul sur l'itinéraire, on doit éviter les autres
                        if len(part1_tolls) > 1 or (len(part1_tolls) == 1 and part1_tolls[0]["id"] != toll["id"]):
                            # On crée une liste des péages à éviter (tous sauf celui qu'on veut)
                            tolls_to_avoid = [t for t in part1_tolls if t["id"] != toll["id"]]
                            
                            if tolls_to_avoid:
                                # On génère des polygones d'évitement pour ces péages
                                with performance_tracker.measure_operation("create_avoidance_polygon"):
                                    avoid_poly = avoidance_multipolygon(tolls_to_avoid)
                                
                                # On refait l'appel en évitant les péages indésirables
                                part1_payload["options"] = {"avoid_polygons": avoid_poly}
                                with performance_tracker.measure_operation("ORS_part1_route_avoid"):
                                    performance_tracker.count_api_call("ORS_alternative_route")
                                    part1_route = self.ors.call_ors(part1_payload)
                                
                                # Vérification finale
                                with performance_tracker.measure_operation("locate_tolls_part1_verify"):
                                    part1_tolls = locate_tolls(part1_route, "data/barriers.csv")["on_route"]
                                unwanted_tolls = [t for t in part1_tolls if t["id"] != toll["id"]]
                                if unwanted_tolls:
                                    print(f"Impossible d'éviter les péages supplémentaires sur la partie 1 pour {toll['id']}")
                                    continue
                        
                        # 2) Partie 2: péage → arrivée (même approche)
                        part2_payload = {
                            "coordinates": [toll_coords, coordinates[1]],
                            "extra_info": ["tollways"]
                        }
                        
                        # D'abord on génère un itinéraire sans restrictions
                        with performance_tracker.measure_operation("ORS_part2_route"):
                            performance_tracker.count_api_call("ORS_alternative_route")
                            part2_route = self.ors.call_ors(part2_payload)
                        
                        # On vérifie quels péages sont sur cet itinéraire
                        with performance_tracker.measure_operation("locate_tolls_part2"):
                            part2_tolls = locate_tolls(part2_route, "data/barriers.csv")["on_route"]
                            add_marginal_cost(part2_tolls, veh_class)
                        
                        # Si le péage cible n'est pas le seul sur l'itinéraire, on doit éviter les autres
                        if len(part2_tolls) > 0:
                            # On crée une liste des péages à éviter (tous les péages de cette partie)
                            tolls_to_avoid = part2_tolls
                            
                            if tolls_to_avoid:
                                # On génère des polygones d'évitement pour ces péages
                                with performance_tracker.measure_operation("create_avoidance_polygon"):
                                    avoid_poly = avoidance_multipolygon(tolls_to_avoid)
                                
                                # On refait l'appel en évitant les péages indésirables
                                part2_payload["options"] = {"avoid_polygons": avoid_poly}
                                try:
                                    with performance_tracker.measure_operation("ORS_part2_route_avoid"):
                                        performance_tracker.count_api_call("ORS_alternative_route")
                                        part2_route = self.ors.call_ors(part2_payload)
                                    
                                    # Vérification finale
                                    with performance_tracker.measure_operation("locate_tolls_part2_verify"):
                                        part2_tolls = locate_tolls(part2_route, "data/barriers.csv")["on_route"]
                                        add_marginal_cost(part2_tolls, veh_class)
                                    unwanted_tolls = [t for t in part2_tolls if t["id"] != toll["id"]]
                                    if unwanted_tolls:
                                        print(f"Impossible d'éviter les péages supplémentaires sur la partie 2 pour {toll['id']}")
                                        continue
                                except Exception as e:
                                    performance_tracker.log_error(f"Erreur lors de l'évitement des péages sur la partie 2: {e}")
                                    print(f"Erreur lors de l'évitement des péages sur la partie 2: {e}")
                                    continue
                        
                        # 3) Fusionner les deux parties de l'itinéraire
                        with performance_tracker.measure_operation("merge_routes"):
                            merged_route = merge_routes(part1_route, part2_route)
                        
                        # 4) Vérifier le coût total et la durée
                        with performance_tracker.measure_operation("calculate_final_metrics"):
                            total_tolls = part1_tolls + part2_tolls
                            add_marginal_cost(total_tolls, veh_class)
                            cost = sum(t.get("cost", 0) for t in total_tolls)
                            duration = merged_route["features"][0]["properties"]["summary"]["duration"]
                            toll_count = len(set(t["id"] for t in total_tolls))
                        
                        # 5) Vérifier si c'est une solution avec exactement un péage
                        if toll_count == 1 and (len(total_tolls) == 0 or toll["id"] == total_tolls[0]["id"]):
                            if cost < best_cost or (cost == best_cost and duration < best_duration):
                                best_cost = cost
                                best_duration = duration
                                best_route = merged_route
                                best_toll_id = toll["id"]
                                print(f"Nouvelle meilleure solution: péage={best_toll_id}, coût={best_cost}€, durée={best_duration/60:.1f}min")
                        
                        # 6) Même si ce n'est pas une solution avec exactement un péage, voir si c'est la solution avec le minimum de péages
                        if toll_count < min_toll_count or (toll_count == min_toll_count and cost < min_toll_cost):
                            min_toll_count = toll_count
                            min_toll_route = merged_route
                            min_toll_cost = cost
                            min_toll_duration = duration
                            min_toll_id = toll["id"]
                            print(f"Nouvelle solution avec minimum de péages: {min_toll_count} péages, péage={min_toll_id}, coût={min_toll_cost}€, durée={min_toll_duration/60:.1f}min")
                            
                    except Exception as e:
                        performance_tracker.log_error(f"Erreur lors du calcul de l'itinéraire via {toll['id']}: {e}")
                        print(f"Erreur lors du calcul de l'itinéraire via {toll['id']}: {e}")
                        continue
            
            return (best_route, best_cost, best_duration, best_toll_id, 
                    min_toll_count, min_toll_route, min_toll_cost, min_toll_duration, min_toll_id)
    
    def handle_one_toll_route(self, coordinates, veh_class, max_comb_size):
        """
        Gère le cas où un seul péage est autorisé.
        Point d'entrée principal pour les routes avec un péage.
        
        Returns:
            dict: Résultat formaté avec fastest, cheapest, min_tolls, status
        """
        with performance_tracker.measure_operation("handle_one_toll_route"):
            # Essayer avec un péage ouvert (approche optimisée pour ce cas précis)
            one_open_result, open_status = self.compute_route_with_one_open_toll(coordinates, veh_class)
            
            # Si on a trouvé une solution avec un péage ouvert, on l'utilise directement
            if one_open_result and open_status == "ONE_OPEN_TOLL_SUCCESS":
                return {
                    "fastest": one_open_result,
                    "cheapest": one_open_result,
                    "min_tolls": one_open_result,
                    "status": open_status
                }
            
            # Si l'approche spécialisée n'a pas fonctionné, utiliser la stratégie générale
            # Import ici pour éviter les imports circulaires
            from src.services.toll.many_tolls_strategy import ManyTollsStrategy
            many_tolls_strategy = ManyTollsStrategy(self.ors)
            many_result = many_tolls_strategy.compute_route_with_many_tolls(coordinates, 2, veh_class, max_comb_size)
            
            # Si solution générale trouvée
            if many_result:
                # Vérifier que les solutions respectent la contrainte originale (max_tolls=1) si possible
                status = "GENERAL_STRATEGY"
                fastest = many_result["fastest"]
                cheapest = many_result["cheapest"]
                min_tolls = many_result["min_tolls"]
                
                # On privilégie les solutions avec 1 péage ou moins si elles existent
                if fastest["toll_count"] > 1 and min_tolls["toll_count"] <= 1:
                    fastest = min_tolls
                    status = "GENERAL_STRATEGY_WITH_MIN_TOLLS"
                    
                if cheapest["toll_count"] > 1 and min_tolls["toll_count"] <= 1:
                    cheapest = min_tolls
                    status = "GENERAL_STRATEGY_WITH_MIN_TOLLS"
                
                return {
                    "fastest": fastest,
                    "cheapest": cheapest,
                    "min_tolls": min_tolls,
                    "status": status
                }
            
            # Aucune solution trouvée
            else:
                from src.services.toll.fallback_strategy import FallbackStrategy
                fallback = FallbackStrategy(self.ors)
                return fallback.get_fallback_route(coordinates, veh_class, "NO_VALID_ROUTE_WITH_MAX_ONE_TOLL")