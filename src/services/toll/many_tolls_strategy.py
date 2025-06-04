"""
many_tolls_strategy.py
---------------------

Stratégie pour calculer des itinéraires avec plusieurs péages autorisés.
Responsabilité unique : optimiser les routes en testant des combinaisons de péages à éviter.
"""

from itertools import combinations
from src.utils.poly_utils import avoidance_multipolygon
from src.utils.route_utils import format_route_result
from src.services.toll.result_manager import RouteResultManager
from benchmark.performance_tracker import performance_tracker
from src.services.toll.route_calculator import RouteCalculator


class ManyTollsStrategy:
    """
    Stratégie pour calculer des itinéraires avec plusieurs péages autorisés.
    Utilise l'optimisation combinatoire pour tester l'évitement de différents groupes de péages.
    """
    
    def __init__(self, ors_service):
        """
        Initialise la stratégie avec un service ORS.
        
        Args:
            ors_service: Instance de ORSService pour les appels API
        """
        self.ors = ors_service
        self.route_calculator = RouteCalculator(ors_service)  # Ajouter cette ligne
    
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
            
            # 1) Premier appel pour obtenir la route de base
            base_route = self.route_calculator.get_base_route_with_tracking(coordinates)

            # 2) Localisation des péages (coûts calculés automatiquement)
            tolls_dict = self.route_calculator.locate_and_cost_tolls(base_route, veh_class, "locate_tolls_many_tolls")
            tolls_on_route = tolls_dict["on_route"]
            tolls_nearby = tolls_dict["nearby"]
            print("Péages sur la route :", tolls_on_route)
            print("Péages proches :", tolls_nearby)

            # 3) Préparation des péages (coûts déjà calculés)
            with performance_tracker.measure_operation("prepare_toll_combinations"):
                all_tolls = tolls_on_route + tolls_nearby
                all_tolls_sorted = sorted(all_tolls, key=lambda t: t.get("cost", 0), reverse=True)

            # Si aucun péage, retourner la route de base
            if not all_tolls_sorted:
                return self._create_base_route_result(base_route)

            # 4) Initialisation du gestionnaire de résultats
            result_manager = RouteResultManager()
            base_metrics = self._get_base_metrics(base_route, veh_class)
            result_manager.initialize_with_base_route(
                base_route, base_metrics["cost"], base_metrics["duration"], 
                base_metrics["toll_count"], max_tolls
            )

            # 5) Test des combinaisons de péages à éviter
            self._test_toll_combinations(
                coordinates, all_tolls_sorted, max_tolls, veh_class, max_comb_size, 
                base_metrics["cost"], result_manager
            )

            # 6) Application du fallback si nécessaire
            result_manager.apply_fallback_if_needed(
                base_route, base_metrics["cost"], base_metrics["duration"], 
                base_metrics["toll_count"], max_tolls
            )

            # 7) Affichage des résultats
            result_manager.log_results(
                base_metrics["toll_count"], base_metrics["cost"], base_metrics["duration"]
            )

            # 8) Vérification finale et retour des résultats
            if not result_manager.has_valid_results():
                print("Aucun itinéraire trouvé respectant la contrainte de max_tolls")
                return None
                
            results = result_manager.get_results()
            results["status"] = "MULTI_TOLL_SUCCESS"
            return results
    
    def _create_base_route_result(self, base_route):
        """Crée un résultat avec la route de base quand aucun péage n'est trouvé."""
        return {
            "fastest": format_route_result(base_route, 0, base_route["features"][0]["properties"]["summary"]["duration"], 0),
            "cheapest": format_route_result(base_route, 0, base_route["features"][0]["properties"]["summary"]["duration"], 0),
            "min_tolls": format_route_result(base_route, 0, base_route["features"][0]["properties"]["summary"]["duration"], 0)
        }
    
    def _get_base_metrics(self, base_route, veh_class):
        """Calcule les métriques de la route de base."""
        with performance_tracker.measure_operation("get_base_metrics"):
            tolls_dict = self.route_calculator.locate_and_cost_tolls(base_route, veh_class, "get_base_metrics")
            base_tolls = tolls_dict["on_route"]
            
            return {
                "cost": sum(t.get("cost", 0) for t in base_tolls),
                "duration": base_route["features"][0]["properties"]["summary"]["duration"],
                "toll_count": len(base_tolls)
            }
    
    def _test_toll_combinations(self, coordinates, all_tolls_sorted, max_tolls, veh_class, 
                              max_comb_size, base_cost, result_manager):
        """Teste toutes les combinaisons de péages à éviter."""
        with performance_tracker.measure_operation("test_toll_combinations"):
            seen_polygons = set()
            tested_combinations = set()
            combination_count = 0
            
            for k in range(1, min(len(all_tolls_sorted), max_comb_size) + 1):
                for to_avoid in combinations(all_tolls_sorted, k):
                    combination_count += 1
                    
                    # Affichage périodique des stats
                    if combination_count % 10 == 0:
                        stats = performance_tracker.get_current_stats()
                        print(f"Progression: {combination_count} combinaisons testées")
                    
                    route_data = self._test_single_combination(
                        coordinates, to_avoid, max_tolls, veh_class, combination_count, k,
                        seen_polygons, tested_combinations, base_cost
                    )
                    
                    if route_data:
                        updated = result_manager.update_with_route(route_data, base_cost)
                        
                        # Arrêt anticipé si coût nul trouvé
                        if updated and route_data["cost"] == 0:
                            break
    
    def _test_single_combination(self, coordinates, to_avoid, max_tolls, veh_class, 
                               combination_count, k, seen_polygons, tested_combinations, base_cost):
        """Teste une combinaison spécifique de péages à éviter."""
        with performance_tracker.measure_operation("test_single_combination", {
            "combination_size": k,
            "combination_count": combination_count
        }):
            sig = tuple(sorted(t["id"] for t in to_avoid))
            if sig in seen_polygons or sig in tested_combinations:
                return None
            
            seen_polygons.add(sig)
            tested_combinations.add(sig)

            # Heuristique d'optimisation précoce
            potential_saving = sum(t.get("cost", 0) for t in to_avoid)
            if base_cost - potential_saving <= 0:
                return None

            # Création du polygone d'évitement
            with performance_tracker.measure_operation("create_avoidance_polygon"):
                poly = avoidance_multipolygon(to_avoid)
            
            # Appel ORS pour l'itinéraire alternatif
            try:
                alt_route = self.route_calculator.get_route_avoiding_polygons_with_tracking(coordinates, poly)
            except Exception:
                return None  # ORS n'a pas trouvé d'itinéraire

            return self._analyze_alternative_route(alt_route, to_avoid, max_tolls, veh_class)
    
    def _analyze_alternative_route(self, alt_route, to_avoid, max_tolls, veh_class):
        """Analyse un itinéraire alternatif et retourne les métriques."""
        with performance_tracker.measure_operation("analyze_alternative_route"):
            alt_tolls_dict = self.route_calculator.locate_and_cost_tolls(alt_route, veh_class, "analyze_alternative_route")
            alt_tolls_on_route = alt_tolls_dict["on_route"]
            
            cost = sum(t.get("cost", 0) for t in alt_tolls_on_route)
            duration = alt_route["features"][0]["properties"]["summary"]["duration"]
            toll_count = len(set(t["id"] for t in alt_tolls_on_route))

            # Vérifications de validité
            avoided_ids = set(str(t["id"]).strip().lower() for t in to_avoid)
            present_ids = set(str(t["id"]).strip().lower() for t in alt_tolls_on_route)
            
            if avoided_ids & present_ids:
                print(f"Attention : certains péages à éviter sont toujours présents : {avoided_ids & present_ids}")
                return None

            if toll_count > max_tolls:
                print(f"Itinéraire ignoré : {toll_count} péages > max_tolls={max_tolls}")
                return None
                
            return format_route_result(alt_route, cost, duration, toll_count)