"""
one_open_toll_strategy.py
------------------------

Stratégie pour calculer des itinéraires passant par exactement un péage à système ouvert.
Responsabilité unique : optimiser les routes avec un seul péage ouvert.
"""

from src.services.toll_locator import get_all_open_tolls_by_proximity
from src.utils.route_utils import is_toll_open_system, merge_routes
from src.services.toll.result_manager import RouteResultManager
from benchmark.performance_tracker import performance_tracker
from src.services.toll.route_calculator import RouteCalculator
from src.services.toll_cost import add_marginal_cost
from src.services.toll.constants import TollOptimizationConfig as Config
from src.services.toll.route_validator import RouteValidator
from src.services.toll.exceptions import ORSConnectionError, NoOpenTollError
from src.services.toll.error_handler import ErrorHandler
from src.services.toll.result_formatter import ResultFormatter
from src.services.ors_config_manager import ORSConfigManager


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
        self.route_calculator = RouteCalculator(ors_service)  # Ajouter cette ligne
    
    def compute_route_with_one_open_toll(self, coordinates, veh_class=Config.DEFAULT_VEH_CLASS):
        """
        Calcule un itinéraire qui passe par exactement un péage à système ouvert.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            veh_class: Classe de véhicule pour le calcul des coûts
            
        Returns:
            tuple: (route_data, status_code)
        """
        with performance_tracker.measure_operation(Config.Operations.COMPUTE_ROUTE_ONE_OPEN_TOLL):
            print(Config.Messages.SEARCH_ONE_OPEN_TOLL)
            
            # Validation précoce des coordonnées
            try:
                ORSConfigManager.validate_coordinates(coordinates)
            except ValueError as e:
                return ErrorHandler.handle_ors_error(e, "validation_coordinates")
            
            # 1) Obtenir la route de base pour identifier les péages à proximité
            try:
                base_route = self.route_calculator.get_base_route_with_tracking(coordinates)
            except Exception as e:
                return ErrorHandler.handle_ors_error(e, "appel initial à ORS")
            
            # 2) Localiser tous les péages sur et à proximité de la route
            with performance_tracker.measure_operation(Config.Operations.LOCATE_TOLLS_ONE_TOLL):
                tolls_dict = self.route_calculator.locate_and_cost_tolls(base_route, veh_class, Config.Operations.LOCATE_TOLLS_ONE_TOLL)
                tolls_on_route = tolls_dict["on_route"]
                tolls_nearby = tolls_dict["nearby"]
                local_tolls = tolls_on_route + tolls_nearby
            
            # 3) Filtrer pour ne garder que les péages à système ouvert à proximité
            with performance_tracker.measure_operation(Config.Operations.FILTER_OPEN_TOLLS):
                nearby_open_tolls = [toll for toll in local_tolls if is_toll_open_system(toll["id"])]
            
            # 4) Initialiser le gestionnaire de résultats
            result_manager = RouteResultManager()
            
            print(Config.Messages.FOUND_OPEN_TOLLS_NEARBY.format(count=len(nearby_open_tolls)))
            
            # 5) Première étape: test avec les péages ouverts à proximité
            if nearby_open_tolls:
                with performance_tracker.measure_operation("test_nearby_open_tolls", {"count": len(nearby_open_tolls)}):
                    self._try_route_with_tolls(coordinates, nearby_open_tolls, veh_class, result_manager)
            
            # 6) Si aucun résultat avec les péages proches, tester avec tous les péages ouverts du réseau
            if not result_manager.has_valid_results():
                print(Config.Messages.NO_OPEN_TOLLS_NEARBY)
                
                # 6.1) Récupérer tous les péages ouverts
                max_distance_m = Config.MAX_DISTANCE_SEARCH_M
                with performance_tracker.measure_operation(Config.Operations.GET_ALL_OPEN_TOLLS, {"max_distance_m": max_distance_m}):
                    all_open_tolls = get_all_open_tolls_by_proximity(base_route, Config.get_barriers_csv_path(), max_distance_m)
                
                if not all_open_tolls:
                    return ErrorHandler.handle_no_open_toll_error(max_distance_m/1000)
                
                print(Config.Messages.FOUND_OPEN_TOLLS_NETWORK.format(count=len(all_open_tolls), distance=max_distance_m/1000))
                
                # 6.2) Les tester dans l'ordre de proximité (limité aux 10 plus proches)
                max_test = Config.MAX_NEARBY_TOLLS_TO_TEST
                with performance_tracker.measure_operation("test_all_open_tolls", {"count": min(max_test, len(all_open_tolls))}):
                    self._try_route_with_tolls(coordinates, all_open_tolls[:max_test], veh_class, result_manager)
            
            # 7) Analyser les résultats et retourner la meilleure solution
            return self._analyze_final_results(result_manager)
    
    def _try_route_with_tolls(self, coordinates, tolls_to_try, veh_class, result_manager):
        """
        Fonction auxiliaire pour tester des itinéraires avec une liste de péages donnée.
        Met à jour le gestionnaire de résultats avec les meilleures solutions trouvées.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            tolls_to_try: Liste des péages à tester
            veh_class: Classe de véhicule
            result_manager: Gestionnaire pour stocker les résultats
        """
        with performance_tracker.measure_operation("try_route_with_tolls", {"tolls_count": len(tolls_to_try)}):
            for toll in tolls_to_try:
                with performance_tracker.measure_operation("test_single_toll", {"toll_id": toll["id"]}):
                    print(f"Test avec péage ouvert: {toll['id']}")
                    
                    route_data = self._calculate_route_through_toll(coordinates, toll, veh_class)
                    
                    if route_data:
                        # Mettre à jour le gestionnaire avec cette nouvelle route
                        # Utiliser un coût de base très élevé pour ne pas limiter les mises à jour
                        result_manager.update_with_route(route_data, float('inf'))
                        
                        # Arrêt anticipé si on trouve une solution avec exactement 1 péage et coût 0
                        if route_data["toll_count"] == 1 and route_data["cost"] == 0:
                            break
    
    def _calculate_route_through_toll(self, coordinates, toll, veh_class):
        """
        Calcule un itinéraire passant par un péage spécifique.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            toll: Données du péage
            veh_class: Classe de véhicule
            
        Returns:
            dict: Données de l'itinéraire ou None si échec
        """
        toll_coords = [toll["longitude"], toll["latitude"]]
        
        try:
            # 1) Calculer partie 1: Départ → péage
            part1_route = self._calculate_route_part(
                [coordinates[0], toll_coords], 
                toll["id"], 
                veh_class, 
                part_name="part1"
            )
            
            if not part1_route:
                return None
            
            # 2) Calculer partie 2: péage → arrivée
            part2_route = self._calculate_route_part(
                [toll_coords, coordinates[1]], 
                toll["id"], 
                veh_class, 
                part_name="part2"
            )
            
            if not part2_route:
                return None
            
            # 3) Fusionner les deux parties
            with performance_tracker.measure_operation(Config.Operations.MERGE_ROUTES):
                merged_route = merge_routes(part1_route["route"], part2_route["route"])
            
            # 4) Calculer les métriques finales
            with performance_tracker.measure_operation(Config.Operations.CALCULATE_FINAL_METRICS):
                total_tolls = part1_route["tolls"] + part2_route["tolls"]
                add_marginal_cost(total_tolls, veh_class)
                cost = sum(t.get("cost", 0) for t in total_tolls)
                duration = merged_route["features"][0]["properties"]["summary"]["duration"]
                toll_count = len(set(t["id"] for t in total_tolls))
            
            # 5) Vérifier la validité (doit contenir le péage cible)
            if not RouteValidator.validate_target_toll_present(
                total_tolls, 
                toll["id"], 
                f"calculate_route_through_{toll['id']}"
            ):
                return None
            
            # 6) Log de la solution trouvée
            if toll_count == 1:
                print(Config.Messages.SOLUTION_ONE_TOLL.format(toll_id=toll['id'], cost=cost, duration=duration/60))
            else:
                print(Config.Messages.SOLUTION_MULTIPLE_TOLLS.format(toll_count=toll_count, toll_id=toll['id'], cost=cost, duration=duration/60))

            return ResultFormatter.format_route_result(merged_route, cost, duration, toll_count, toll["id"])
    
        except Exception as e:
            return ErrorHandler.handle_route_calculation_error(e, toll_id=toll['id'])
    
    def _calculate_route_part(self, coordinates, target_toll_id, veh_class, part_name):
        """
        Calcule une partie d'itinéraire en évitant les péages indésirables.
        
        Args:
            coordinates: Coordonnées de la partie [départ, arrivée]
            target_toll_id: ID du péage cible à conserver
            veh_class: Classe de véhicule (non utilisé ici mais gardé pour compatibilité)
            part_name: Nom de la partie pour le logging
            
        Returns:
            dict: {"route": route_data, "tolls": tolls_list} ou None
        """
        return self.route_calculator.calculate_route_avoiding_unwanted_tolls(
            coordinates, target_toll_id, part_name
        )
    
    def _analyze_final_results(self, result_manager):
        """Analyse les résultats finaux et retourne la meilleure solution."""
        if not result_manager.has_valid_results():
            return None, Config.StatusCodes.NO_VALID_OPEN_TOLL_ROUTE
        
        results = result_manager.get_results()
        
        # Privilégier les solutions avec exactement 1 péage
        for result_type in ["min_tolls", "cheapest", "fastest"]:
            result = results[result_type]
            if result["route"] and result["toll_count"] == 1:
                return result, Config.StatusCodes.ONE_OPEN_TOLL_SUCCESS
        
        # Si aucune solution avec exactement 1 péage, prendre celle avec le minimum de péages
        min_tolls_result = results["min_tolls"]
        if min_tolls_result["route"]:
            print(Config.Messages.NO_EXACT_ONE_TOLL.format(toll_count=min_tolls_result['toll_count']))
            return min_tolls_result, Config.StatusCodes.MINIMUM_TOLLS_SOLUTION
        
        return None, Config.StatusCodes.NO_VALID_OPEN_TOLL_ROUTE
    
    def handle_one_toll_route(self, coordinates, veh_class, max_comb_size):
        """
        Gère le cas où un seul péage est autorisé.
        Point d'entrée principal pour les routes avec un péage.
        
        Returns:
            dict: Résultat formaté avec fastest, cheapest, min_tolls, status
        """
        with performance_tracker.measure_operation(Config.Operations.HANDLE_ONE_TOLL_ROUTE):
            # Essayer avec un péage ouvert (approche optimisée pour ce cas précis)
            one_open_result, open_status = self.compute_route_with_one_open_toll(coordinates, veh_class)
            
            # Si on a trouvé une solution avec un péage ouvert, on l'utilise directement
            if one_open_result and open_status == Config.StatusCodes.ONE_OPEN_TOLL_SUCCESS:
                return ResultFormatter.format_optimization_results(
                    fastest=one_open_result,
                    cheapest=one_open_result,
                    min_tolls=one_open_result,
                    status=open_status
                )
            
            # Si l'approche spécialisée n'a pas fonctionné, utiliser la stratégie générale
            from src.services.toll.many_tolls_strategy import ManyTollsStrategy
            many_tolls_strategy = ManyTollsStrategy(self.ors)
            many_result = many_tolls_strategy.compute_route_with_many_tolls(coordinates, 2, veh_class, max_comb_size)
            
            # Si solution générale trouvée
            if many_result:
                # Vérifier que les solutions respectent la contrainte originale (max_tolls=1) si possible
                status = Config.StatusCodes.GENERAL_STRATEGY
                fastest = many_result["fastest"]
                cheapest = many_result["cheapest"]
                min_tolls = many_result["min_tolls"]
                
                # On privilégie les solutions avec 1 péage ou moins si elles existent
                if fastest["toll_count"] > 1 and min_tolls["toll_count"] <= 1:
                    fastest = min_tolls
                    status = Config.StatusCodes.GENERAL_STRATEGY_WITH_MIN_TOLLS
                    
                if cheapest["toll_count"] > 1 and min_tolls["toll_count"] <= 1:
                    cheapest = min_tolls
                    status = Config.StatusCodes.GENERAL_STRATEGY_WITH_MIN_TOLLS
                
                return ResultFormatter.format_optimization_results(
                    fastest=fastest,
                    cheapest=cheapest,
                    min_tolls=min_tolls,
                    status=status
                )
            
            # Aucune solution trouvée
            else:
                from src.services.toll.fallback_strategy import FallbackStrategy
                fallback = FallbackStrategy(self.ors)
                return fallback.get_fallback_route(coordinates, veh_class, Config.StatusCodes.NO_VALID_ROUTE_WITH_MAX_ONE_TOLL)