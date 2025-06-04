"""
toll_strategies.py
-----------------

Stratégies pour calculer des itinéraires avec des contraintes sur le nombre de péages.
Intègre le système de mesure des performances pour optimiser les appels.
"""

import copy
import requests
from itertools import combinations
from src.services.toll_locator import locate_tolls, get_all_open_tolls_by_proximity
from src.services.toll_cost import add_marginal_cost
from src.utils.poly_utils import avoidance_multipolygon
from src.utils.route_utils import is_toll_open_system, merge_routes, format_route_result
from benchmark.performance_tracker import performance_tracker

class TollRouteOptimizer:
    """
    Optimiseur d'itinéraires avec contraintes sur le nombre de péages.
    Intègre le tracking des performances pour analyser et optimiser les appels.
    """
    
    def __init__(self, ors_service):
        """
        Initialise l'optimiseur avec un service ORS.
        
        Args:
            ors_service: Instance de ORSService pour les appels API
        """
        self.ors = ors_service
    
    def compute_route_with_toll_limit(self, coordinates, max_tolls, veh_class="c1", max_comb_size=2):
        """
        Calcule un itinéraire avec une limite sur le nombre de péages.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            max_tolls: Nombre maximum de péages autorisés
            veh_class: Classe de véhicule pour le calcul des coûts
            max_comb_size: Limite pour les combinaisons de péages à éviter
            
        Returns:
            dict: Résultats optimisés (fastest, cheapest, min_tolls, status)
        """
        with performance_tracker.measure_operation("compute_route_with_toll_limit", {
            "max_tolls": max_tolls,
            "veh_class": veh_class,
            "max_comb_size": max_comb_size
        }):
            print(f"=== Calcul d'itinéraire avec un maximum de {max_tolls} péages ===")
            
            # Cas spécial 1: Aucun péage autorisé
            if max_tolls == 0:
                return self._handle_no_toll_route(coordinates, veh_class)
                
            # Cas spécial 2: Un seul péage autorisé
            elif max_tolls == 1:
                return self._handle_one_toll_route(coordinates, veh_class, max_comb_size)
                
            # Cas général: Plusieurs péages autorisés
            else:
                result = self.compute_route_with_many_tolls(coordinates, max_tolls, veh_class, max_comb_size)
                
                if result:
                    result["status"] = "MULTI_TOLL_SUCCESS"
                    return result
                else:
                    # Fallback avec la route de base
                    return self._get_fallback_route(coordinates, veh_class, "NO_VALID_ROUTE_WITH_MAX_TOLLS")
    
    def _handle_no_toll_route(self, coordinates, veh_class):
        """
        Gère le cas où aucun péage n'est autorisé.
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
                # Fallback : route de base (mais avec statut d'erreur)
                return self._get_fallback_route(coordinates, veh_class, status)
    
    def _handle_one_toll_route(self, coordinates, veh_class, max_comb_size):
        """
        Gère le cas où un seul péage est autorisé.
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
            
            # Si l'approche spécialisée n'a pas fonctionné, on essaie l'approche générale
            # On autorise max_tolls + 1 péages (donc 2 péages) pour augmenter les chances de trouver une solution
            many_result = self.compute_route_with_many_tolls(coordinates, 2, veh_class, max_comb_size)
            
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
                return self._get_fallback_route(coordinates, veh_class, "NO_VALID_ROUTE_WITH_MAX_ONE_TOLL")
    
    def _get_fallback_route(self, coordinates, veh_class, status):
        """
        Génère une route de base comme solution de repli lorsqu'aucune solution n'est trouvée.
        """
        with performance_tracker.measure_operation("get_fallback_route"):
            with performance_tracker.measure_operation("ORS_base_route_fallback"):
                performance_tracker.count_api_call("ORS_base_route")
                base_route = self.ors.get_base_route(coordinates)
            
            with performance_tracker.measure_operation("locate_tolls_fallback"):
                tolls_on_route = locate_tolls(base_route, "data/barriers.csv")["on_route"]
                add_marginal_cost(tolls_on_route, veh_class)
            
            base_cost = sum(t.get("cost", 0) for t in tolls_on_route)
            base_duration = base_route["features"][0]["properties"]["summary"]["duration"]
            
            result = format_route_result(
                base_route,
                base_cost,
                base_duration,
                len(tolls_on_route)
            )
            
            return {
                "fastest": result,
                "cheapest": result,
                "min_tolls": result,
                "status": status
            }
    
    def compute_route_no_toll(self, coordinates, veh_class):
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
    
    def compute_route_with_one_open_toll(self, coordinates, veh_class):
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
                    best_route, best_cost, best_duration, best_toll_id, min_toll_count, min_toll_route, min_toll_cost, min_toll_duration, min_toll_id = self.try_route_with_tolls(
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
                    best_route, best_cost, best_duration, best_toll_id, min_toll_count, min_toll_route, min_toll_cost, min_toll_duration, min_toll_id = self.try_route_with_tolls(
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
    
    def try_route_with_tolls(
        self,
        coordinates, 
        tolls_to_try, 
        veh_class = "c1",
        current_best_route = None,
        current_best_cost = float('inf'),
        current_best_duration = float('inf'),
        current_best_toll_id = None,
        current_min_toll_count = float('inf'),
        current_min_toll_route = None,
        current_min_toll_cost = float('inf'),
        current_min_toll_duration = float('inf'),
        current_min_toll_id = None
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
    
    def compute_route_with_many_tolls(self, coordinates, max_tolls, veh_class="c1", max_comb_size=2):
        """
        Calcule des itinéraires avec un nombre de péages ≤ max_tolls (où max_tolls > 1).
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            max_tolls: Nombre maximum de péages autorisés
            veh_class: Classe de véhicule pour le calcul des coûts
            max_comb_size: Limite pour les combinaisons de péages à éviter
            
        Returns:
            dict: Les meilleures routes trouvées (fastest, cheapest, min_tolls)
        """
        with performance_tracker.measure_operation("compute_route_with_many_tolls", {
            "max_tolls": max_tolls,
            "max_comb_size": max_comb_size
        }):
            print(f"Recherche d'itinéraires avec max {max_tolls} péages...")
            
            # 1) Premier appel (rapide)
            with performance_tracker.measure_operation("ORS_base_route_many_tolls"):
                performance_tracker.count_api_call("ORS_base_route")
                base_route = self.ors.get_base_route(coordinates)

            # 2) Localisation + coûts
            with performance_tracker.measure_operation("locate_tolls_many_tolls"):
                tolls_dict = locate_tolls(base_route, "data/barriers.csv")
                tolls_on_route = tolls_dict["on_route"]
                tolls_nearby = tolls_dict["nearby"]
                print("Péages sur la route :", tolls_on_route)
                print("Péages proches :", tolls_nearby)

            # On fusionne les deux listes pour générer toutes les combinaisons
            with performance_tracker.measure_operation("prepare_toll_combinations"):
                all_tolls = tolls_on_route + tolls_nearby
                add_marginal_cost(all_tolls, veh_class)
                all_tolls_sorted = sorted(all_tolls, key=lambda t: t.get("cost", 0), reverse=True)

            # Si aucun péage, on retourne la route de base
            if not all_tolls_sorted:
                return {
                    "fastest": format_route_result(base_route, 0, base_route["features"][0]["properties"]["summary"]["duration"], 0),
                    "cheapest": format_route_result(base_route, 0, base_route["features"][0]["properties"]["summary"]["duration"], 0),
                    "min_tolls": format_route_result(base_route, 0, base_route["features"][0]["properties"]["summary"]["duration"], 0)
                }

            # Initialisation : best_cheap = coût de base, best_fast = None
            with performance_tracker.measure_operation("initialize_base_metrics"):
                base_tolls = locate_tolls(base_route, "data/barriers.csv")["on_route"]
                add_marginal_cost(base_tolls, veh_class)
                base_cost = sum(t.get("cost", 0) for t in base_tolls)
                base_duration = base_route["features"][0]["properties"]["summary"]["duration"]
                base_toll_count = len(base_tolls)
                
                # Si le nombre de péages de la route de base est déjà <= max_tolls, c'est un bon point de départ
                if base_toll_count <= max_tolls:
                    best_cheap = format_route_result(base_route, base_cost, base_duration, base_toll_count)
                    best_fast = format_route_result(base_route, base_cost, base_duration, base_toll_count)
                    best_min_tolls = format_route_result(base_route, base_cost, base_duration, base_toll_count)
                else:
                    # Sinon, on initialise avec des valeurs par défaut qui seront remplacées
                    best_cheap = {
                        "route": None,
                        "cost": float('inf'),
                        "duration": float('inf'),
                        "toll_count": float('inf')
                    }
                    best_fast = {
                        "route": None,
                        "cost": float('inf'),
                        "duration": float('inf'),
                        "toll_count": float('inf')
                    }
                    best_min_tolls = {
                        "route": None,
                        "cost": float('inf'),
                        "duration": float('inf'),
                        "toll_count": float('inf')
                    }

            seen_polygons = set()
            tested_combinations = set()

            # 3) Génère toutes les combinaisons de péages à éviter (taille 1 à max_comb_size)
            with performance_tracker.measure_operation("test_toll_combinations"):
                combination_count = 0
                for k in range(1, min(len(all_tolls_sorted), max_comb_size) + 1):
                    for to_avoid in combinations(all_tolls_sorted, k):
                        combination_count += 1
                        
                        # Affichage périodique des stats
                        if combination_count % 10 == 0:  # Tous les 10 tests
                            stats = performance_tracker.get_current_stats()
                            print(f"🔄 Progression: {combination_count} combinaisons testées")
                        
                        with performance_tracker.measure_operation("test_single_combination", {
                            "combination_size": k,
                            "combination_count": combination_count
                        }):
                            sig = tuple(sorted(t["id"] for t in to_avoid))
                            if sig in seen_polygons:
                                continue
                            seen_polygons.add(sig)

                            # Heuristique : coût potentiel économisé
                            potential_saving = sum(t.get("cost", 0) for t in to_avoid)
                            # Si l'économie potentielle ne permet pas de passer sous le coût de base, on skip
                            if base_cost - potential_saving <= 0:
                                continue
                            # Caching/mémorisation
                            if sig in tested_combinations:
                                continue
                            tested_combinations.add(sig)

                            with performance_tracker.measure_operation("create_avoidance_polygon"):
                                poly = avoidance_multipolygon(to_avoid)
                            
                            try:
                                with performance_tracker.measure_operation("ORS_alternative_route"):
                                    performance_tracker.count_api_call("ORS_alternative_route")
                                    alt_route = self.ors.get_route_avoiding_polygons(coordinates, poly)
                            except Exception:
                                continue  # ORS n'a pas trouvé d'itinéraire

                            with performance_tracker.measure_operation("analyze_alternative_route"):
                                alt_tolls_dict = locate_tolls(alt_route, "data/barriers.csv")
                                alt_tolls_on_route = alt_tolls_dict["on_route"]
                                add_marginal_cost(alt_tolls_on_route, veh_class)
                                cost = sum(t.get("cost", 0) for t in alt_tolls_on_route)
                                duration = alt_route["features"][0]["properties"]["summary"]["duration"]
                                toll_count = len(set(t["id"] for t in alt_tolls_on_route))

                                # Vérification : les péages à éviter ne doivent pas être présents
                                avoided_ids = set(str(t["id"]).strip().lower() for t in to_avoid)
                                present_ids = set(str(t["id"]).strip().lower() for t in alt_tolls_on_route)
                                print(f"Vérif exclusion : à éviter={avoided_ids}, présents={present_ids}")
                                if avoided_ids & present_ids:
                                    print(f"Attention : certains péages à éviter sont toujours présents dans l'itinéraire alternatif : {avoided_ids & present_ids}")
                                    continue  # On ignore cet itinéraire

                                # Contrainte : respecter max_tolls
                                if toll_count > max_tolls:
                                    print(f"Itinéraire ignoré : {toll_count} péages > max_tolls={max_tolls}")
                                    continue
                                    
                                # Création du dictionnaire pour cet itinéraire
                                route_data = format_route_result(alt_route, cost, duration, toll_count)

                                # Mise à jour de l'itinéraire avec le moins de péages
                                if toll_count < best_min_tolls["toll_count"]:
                                    best_min_tolls = route_data

                                # Si l'itinéraire est moins cher que le best_cheap actuel
                                if cost < best_cheap["cost"]:
                                    best_cheap = route_data
                                    # Si best_fast n'est pas encore défini ou si cet itinéraire est plus rapide et respecte le budget
                                    if best_fast["route"] is None or duration < best_fast["duration"]:
                                        best_fast = route_data
                                    # Arrêt anticipé si coût nul
                                    if cost == 0:
                                        break
                                
                                # Pour le plus rapide : on ne retient que les itinéraires dont le coût <= coût de base
                                if cost <= base_cost:
                                    if best_fast["route"] is None or duration < best_fast["duration"]:
                                        best_fast = route_data

            # Fallback si rien trouvé (mais seulement si base_toll_count <= max_tolls)
            if best_fast["route"] is None and base_toll_count <= max_tolls:
                best_fast = format_route_result(base_route, base_cost, base_duration, base_toll_count)
                
            if best_cheap["route"] is None and base_toll_count <= max_tolls:
                best_cheap = format_route_result(base_route, base_cost, base_duration, base_toll_count)
                
            if best_min_tolls["route"] is None and base_toll_count <= max_tolls:
                best_min_tolls = format_route_result(base_route, base_cost, base_duration, base_toll_count)

            # Affichage des résultats
            print(f"[RESULT] Base: {base_toll_count} péages, coût={base_cost}€, durée={base_duration/60:.1f} min")
            
            if best_cheap["route"]:
                print(f"[RESULT] Cheapest: {best_cheap['toll_count']} péages, coût={best_cheap['cost']}€, durée={best_cheap['duration']/60:.1f} min")
            else:
                print("[RESULT] Pas d'itinéraire économique trouvé respectant la contrainte de max_tolls")
                
            if best_fast["route"]:
                print(f"[RESULT] Fastest: {best_fast['toll_count']} péages, coût={best_fast['cost']}€, durée={best_fast['duration']/60:.1f} min")
            else:
                print("[RESULT] Pas d'itinéraire rapide trouvé respectant la contrainte de max_tolls")
                
            if best_min_tolls["route"]:
                print(f"[RESULT] Minimum tolls: {best_min_tolls['toll_count']} péages, coût={best_min_tolls['cost']}€, durée={best_min_tolls['duration']/60:.1f} min")
            else:
                print("[RESULT] Pas d'itinéraire avec un minimum de péages trouvé")

            # Si aucune solution trouvée, retourner None ou statut d'erreur
            if not (best_fast["route"] or best_cheap["route"] or best_min_tolls["route"]):
                print("Aucun itinéraire trouvé respectant la contrainte de max_tolls")
                return None
                
            # Formater les résultats avec structure complète
            result = {
                "fastest": best_fast,
                "cheapest": best_cheap,
                "min_tolls": best_min_tolls
            }
            
        return result
