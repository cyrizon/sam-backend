"""
many_tolls_strategy.py
---------------------

Stratégie pour calculer des itinéraires avec plusieurs péages autorisés.
Responsabilité unique : optimiser les routes en testant des combinaisons de péages à éviter.
"""

from itertools import combinations
from src.utils.poly_utils import avoidance_multipolygon
from src.services.common.result_formatter import ResultFormatter
from src.services.toll.result_manager import RouteResultManager
from benchmark.performance_tracker import performance_tracker
from src.services.toll.route_calculator import RouteCalculator
from src.services.toll.constants import TollOptimizationConfig as Config
from src.services.toll.route_validator import RouteValidator
from src.services.toll.error_handler import ErrorHandler
from src.services.ors_config_manager import ORSConfigManager


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
    
    def compute_route_with_many_tolls(self, coordinates, max_tolls, veh_class=Config.DEFAULT_VEH_CLASS, max_comb_size=Config.DEFAULT_MAX_COMB_SIZE):
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
        # Validation précoce des coordonnées
        try:
            ORSConfigManager.validate_coordinates(coordinates)
        except ValueError as e:
            return ErrorHandler.handle_ors_error(e, "validation_coordinates")
        
        with performance_tracker.measure_operation(Config.Operations.COMPUTE_ROUTE_MANY_TOLLS, {
            "max_tolls": max_tolls,
            "max_comb_size": max_comb_size
        }):
            print(Config.Messages.SEARCH_MANY_TOLLS.format(max_tolls=max_tolls))
            
            # 1) Premier appel pour obtenir la route de base
            base_route = self.route_calculator.get_base_route_with_tracking(coordinates)

            # 2) Localisation des péages (coûts calculés automatiquement)
            tolls_dict = self.route_calculator.locate_and_cost_tolls(base_route, veh_class, Config.Operations.LOCATE_TOLLS_MANY_TOLLS)
            tolls_on_route = tolls_dict["on_route"]
            tolls_nearby = tolls_dict["nearby"]
            print(Config.Messages.TOLLS_ON_ROUTE, tolls_on_route)
            print(Config.Messages.TOLLS_NEARBY, tolls_nearby)

            # 3) Préparation des péages (coûts déjà calculés)
            with performance_tracker.measure_operation(Config.Operations.PREPARE_TOLL_COMBINATIONS):
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
                print(Config.Messages.NO_ROUTE_FOUND_MAX_TOLLS)
                return None
                
            results = result_manager.get_results()
            return ResultFormatter.format_optimization_results(
                fastest=results["fastest"],
                cheapest=results["cheapest"],
                min_tolls=results["min_tolls"],
                status=Config.StatusCodes.MULTI_TOLL_SUCCESS
            )
    
    def _create_base_route_result(self, base_route):
        """Crée un résultat avec la route de base quand aucun péage n'est trouvé."""
        base_result = ResultFormatter.format_route_result(
            base_route, 0, 
            base_route["features"][0]["properties"]["summary"]["duration"], 
            0
        )
        
        return ResultFormatter.format_optimization_results(
            fastest=base_result,
            cheapest=base_result,
            min_tolls=base_result,
            status=Config.StatusCodes.MULTI_TOLL_SUCCESS
        )
    
    def _get_base_metrics(self, base_route, veh_class):
        """Calcule les métriques de la route de base."""
        with performance_tracker.measure_operation(Config.Operations.GET_BASE_METRICS):
            tolls_dict = self.route_calculator.locate_and_cost_tolls(base_route, veh_class, Config.Operations.GET_BASE_METRICS)
            base_tolls = tolls_dict["on_route"]
            
            return {
                "cost": sum(t.get("cost", 0) for t in base_tolls),
                "duration": base_route["features"][0]["properties"]["summary"]["duration"],
                "toll_count": len(base_tolls)
            }
    
    def _test_toll_combinations(self, coordinates, all_tolls_sorted, max_tolls, veh_class, 
                              max_comb_size, base_cost, result_manager):
        """Teste toutes les combinaisons de péages à éviter."""
        with performance_tracker.measure_operation(Config.Operations.TEST_TOLL_COMBINATIONS):
            seen_polygons = set()
            tested_combinations = set()
            combination_count = 0
            
            for k in range(1, min(len(all_tolls_sorted), max_comb_size) + 1):
                for to_avoid in combinations(all_tolls_sorted, k):
                    combination_count += 1
                    
                    # Affichage périodique des stats
                    if combination_count % Config.COMBINATION_PROGRESS_INTERVAL == 0:
                        stats = performance_tracker.get_current_stats()
                        print(Config.Messages.PROGRESS_COMBINATIONS.format(count=combination_count))
                    
                    route_data = self._test_single_combination(
                        coordinates, to_avoid, max_tolls, veh_class, combination_count, k,
                        seen_polygons, tested_combinations, base_cost
                    )
                    
                    if route_data:
                        updated = result_manager.update_with_route(route_data, base_cost)
                        
                        # Arrêt anticipé si coût nul trouvé
                        if Config.EARLY_STOP_ZERO_COST and updated and route_data["cost"] == 0:
                            break
    
    def _test_single_combination(self, coordinates, to_avoid, max_tolls, veh_class, 
                               combination_count, k, seen_polygons, tested_combinations, base_cost):
        """Teste une combinaison spécifique de péages à éviter."""
        with performance_tracker.measure_operation(Config.Operations.TEST_SINGLE_COMBINATION, {
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
            with performance_tracker.measure_operation(Config.Operations.CREATE_AVOIDANCE_POLYGON):
                poly = avoidance_multipolygon(to_avoid)
            
            # Appel ORS pour l'itinéraire alternatif
            try:
                alt_route = self.route_calculator.get_route_avoiding_polygons_with_tracking(coordinates, poly)
            except Exception as e:
                ErrorHandler.log_operation_failure(
                    f"test_combination_{combination_count}", 
                    f"Impossible de calculer une route alternative: {e}"
                )
                return None

            return self._analyze_alternative_route(alt_route, to_avoid, max_tolls, veh_class)
    
    def _analyze_alternative_route(self, alt_route, to_avoid, max_tolls, veh_class):
        """Analyse un itinéraire alternatif et retourne les métriques."""
        with performance_tracker.measure_operation(Config.Operations.ANALYZE_ALTERNATIVE_ROUTE):
            alt_tolls_dict = self.route_calculator.locate_and_cost_tolls(alt_route, veh_class, Config.Operations.ANALYZE_ALTERNATIVE_ROUTE)
            alt_tolls_on_route = alt_tolls_dict["on_route"]
            
            cost = sum(t.get("cost", 0) for t in alt_tolls_on_route)
            duration = alt_route["features"][0]["properties"]["summary"]["duration"]
            toll_count = len(set(t["id"] for t in alt_tolls_on_route))

            # Validation complète avec le RouteValidator
            if not RouteValidator.validate_all_constraints(
                alt_tolls_on_route, 
                toll_count, 
                max_tolls, 
                avoided_tolls=to_avoid,
                operation_name="analyze_alternative_route"
            ):
                return None
                
            return ResultFormatter.format_route_result(alt_route, cost, duration, toll_count)