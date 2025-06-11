"""
percentage_budget_strategy.py
----------------------------

Stratégie pour calculer des itinéraires avec contrainte de budget en pourcentage.
Responsabilité unique : optimiser les routes selon un pourcentage du coût de base.
"""

from benchmark.performance_tracker import performance_tracker
from src.services.budget.constants import BudgetOptimizationConfig as Config
from src.services.common.result_formatter import ResultFormatter
from src.services.budget.result_manager import BudgetRouteResultManager as RouteResultManager
from src.services.budget.route_calculator import BudgetRouteCalculator
from src.services.budget.error_handler import BudgetErrorHandler
from src.services.ors_config_manager import ORSConfigManager
from src.services.common.budget_messages import BudgetMessages
from src.services.common.common_messages import CommonMessages
from src.services.toll_locator import locate_tolls, get_all_open_tolls_by_proximity
from src.services.budget.cached_toll_cost import add_marginal_cost_cached, log_toll_cost_cache_stats
from src.utils.poly_utils import avoidance_multipolygon
from itertools import combinations


class PercentageBudgetStrategy:
    """
    Stratégie pour calculer des itinéraires avec contrainte budgétaire en pourcentage.
    """
    
    def __init__(self, ors_service):
        """
        Initialise la stratégie avec un service ORS.
        
        Args:
            ors_service: Instance de ORSService pour les appels API        """
        self.ors = ors_service
        self.route_calculator = BudgetRouteCalculator(ors_service)
    
    def compute_percentage_budget_route(self, coordinates, max_price_percent, veh_class=Config.DEFAULT_VEH_CLASS, max_comb_size=Config.DEFAULT_MAX_COMB_SIZE):
        """
        Calcule un itinéraire avec contrainte budgétaire en pourcentage.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            max_price_percent: Pourcentage du coût de base (0.8 = 80%)
            veh_class: Classe de véhicule
            max_comb_size: Limite pour les combinaisons de péages à éviter
            
        Returns:
            dict: Résultat formaté ou erreur
        """
        # Validation précoce des coordonnées
        try:
            ORSConfigManager.validate_coordinates(coordinates)
        except ValueError as e:
            return BudgetErrorHandler.handle_ors_error(e, "validation_coordinates")
          # Validation du pourcentage
        if max_price_percent < 0 or max_price_percent > 1:
            return BudgetErrorHandler.handle_ors_error(
                ValueError(f"Le pourcentage doit être entre 0 et 1: {max_price_percent}"),
                "validation_percentage"
            )
        
        with performance_tracker.measure_operation(Config.Operations.HANDLE_PERCENTAGE_BUDGET_ROUTE):
            print(BudgetMessages.SEARCH_PERCENTAGE_BUDGET.format(percent=max_price_percent*100))
            
            try:
                # 1) Obtenir la route de base pour calculer le coût de référence
                base_route = self.route_calculator.get_base_route_with_tracking(coordinates)
                # 2) Calculer le coût de base et définir la limite budgétaire
                base_cost, base_duration, base_toll_count = self._get_base_metrics(base_route, veh_class)
                price_limit = base_cost * max_price_percent
                
                print(BudgetMessages.BASE_ROUTE_COST.format(cost=base_cost))
                print(BudgetMessages.BUDGET_LIMIT.format(limit=price_limit))
                
                # 2.5) Vérification de faisabilité pour budget pourcentage
                from src.services.budget.feasibility_checker import BudgetFeasibilityChecker
                feasibility_checker = BudgetFeasibilityChecker(self.route_calculator.ors)
                
                # Obtenir les péages pour la vérification de faisabilité
                tolls_dict = self.route_calculator.locate_and_cost_tolls(base_route, veh_class)
                
                if feasibility_checker.check_percentage_budget_feasibility(base_cost, max_price_percent, tolls_dict):
                    print("🚫 Budget pourcentage impossible - Retour statut spécial")
                    return {
                        "fastest": None,
                        "cheapest": None, 
                        "min_tolls": None,
                        "status": Config.StatusCodes.PERCENTAGE_BUDGET_IMPOSSIBLE,
                        "base_route": base_route,
                        "base_cost": base_cost,
                        "base_duration": base_duration,
                        "base_toll_count": base_toll_count
                    }
                
                # 3) Vérifier si la route de base respecte déjà la contrainte
                if base_cost <= price_limit:
                    print(CommonMessages.BUDGET_SATISFIED)
                    route_result = ResultFormatter.format_route_result(
                        base_route, base_cost, base_duration, base_toll_count
                    )
                    return ResultFormatter.format_uniform_result(
                        route_result, Config.StatusCodes.BUDGET_ALREADY_SATISFIED
                    )
                
                # 4) Rechercher des alternatives moins chères
                optimization_result = self._optimize_route_for_percentage_budget(
                    coordinates, base_route, base_cost, price_limit, veh_class, max_comb_size
                )
                
                return optimization_result
                
            except Exception as e:
                print(f"Erreur lors du calcul avec contrainte de pourcentage: {e}")
                return BudgetErrorHandler.handle_ors_error(e, Config.Operations.HANDLE_PERCENTAGE_BUDGET_ROUTE)
    
    def _get_base_metrics(self, base_route, veh_class):
        """Calcule les métriques de la route de base."""
        with performance_tracker.measure_operation(Config.Operations.GET_BASE_METRICS_PERCENTAGE):
            tolls_dict = self.route_calculator.locate_and_cost_tolls(
                base_route, veh_class, Config.Operations.LOCATE_TOLLS_PERCENTAGE_BUDGET
            )
            tolls_on_route = tolls_dict["on_route"]
            
            base_cost = sum(t.get("cost", 0) for t in tolls_on_route)
            base_duration = base_route["features"][0]["properties"]["summary"]["duration"]
            base_toll_count = len(tolls_on_route)
            
            return base_cost, base_duration, base_toll_count
    
    def _optimize_route_for_percentage_budget(self, coordinates, base_route, base_cost, price_limit, veh_class, max_comb_size):
        """Optimise la route pour respecter la contrainte budgétaire en pourcentage."""
        with performance_tracker.measure_operation(Config.Operations.OPTIMIZE_PERCENTAGE_BUDGET):
            
            # Initialiser le gestionnaire de résultats avec la route de base
            result_manager = RouteResultManager()
            base_route_data = ResultFormatter.format_route_result(
                base_route, base_cost, 
                base_route["features"][0]["properties"]["summary"]["duration"],
                len(locate_tolls(base_route, Config.get_barriers_csv_path())["on_route"])
            )
            result_manager.update_with_route(base_route_data, float('inf'))  # Pas de limite pour le base
            
            # Localiser tous les péages disponibles pour optimisation
            tolls_dict = locate_tolls(base_route, Config.get_barriers_csv_path())
            tolls_on_route = tolls_dict["on_route"]
            tolls_nearby = tolls_dict["nearby"]
            
            # Enrichir avec les péages à proximité
            max_distance_m = Config.MAX_DISTANCE_SEARCH_M
            all_tolls_nearby = get_all_open_tolls_by_proximity(base_route, Config.get_barriers_csv_path(), max_distance_m)
            if not all_tolls_nearby:
                all_tolls_nearby = []
              # Combiner tous les péages et calculer leurs coûts avec cache
            all_tolls = tolls_on_route + tolls_nearby + all_tolls_nearby
            add_marginal_cost_cached(all_tolls, veh_class)
            all_tolls_sorted = sorted(all_tolls, key=lambda t: t.get("cost", 0), reverse=True)
            
            if not all_tolls_sorted:
                print("Aucun péage trouvé pour l'optimisation.")
                return ResultFormatter.format_uniform_result(
                    base_route_data, Config.StatusCodes.NO_TOLLS_FOUND
                )
            
            print(f"Péages disponibles pour optimisation: {len(all_tolls_sorted)}")
            
            # Tester l'évitement des péages individuellement
            self._test_individual_toll_avoidance(
                coordinates, all_tolls_sorted, price_limit, veh_class, result_manager
            )
            
            # Tester des combinaisons de péages si nécessaire
            if not self._has_budget_compliant_route(result_manager, price_limit):
                self._test_toll_combinations(
                    coordinates, all_tolls_sorted, price_limit, veh_class, max_comb_size, result_manager
                )
            
            # Construire le résultat final
            return self._build_percentage_budget_result(result_manager, price_limit)
    
    def _test_individual_toll_avoidance(self, coordinates, all_tolls_sorted, price_limit, veh_class, result_manager):
        """Teste l'évitement des péages individuellement."""
        with performance_tracker.measure_operation(Config.Operations.TEST_INDIVIDUAL_TOLLS_PERCENTAGE):
            print("Test de l'évitement des péages individuels...")
            
            for toll in all_tolls_sorted:
                if toll.get("cost", 0) <= 0:
                    continue
                
                print(f"Test d'évitement du péage: {toll['id']} (coût: {toll.get('cost', 0)}€)")
                
                route_data = self._test_single_toll_avoidance(coordinates, toll, veh_class)
                if route_data:
                    updated = result_manager.update_with_route(route_data, float('inf'))
                    
                    # Arrêt anticipé si on trouve une solution dans le budget et gratuite
                    if updated and route_data["cost"] == 0:
                        print("Route gratuite trouvée !")
                        break
                    
                    # Arrêt anticipé si on a une solution dans le budget
                    if route_data["cost"] <= price_limit:
                        print(f"Solution dans le budget trouvée: {route_data['cost']}€ ≤ {price_limit}€")
    
    def _test_single_toll_avoidance(self, coordinates, toll, veh_class):
        """Teste l'évitement d'un péage spécifique."""
        try:
            # Créer le polygone d'évitement
            poly = avoidance_multipolygon([toll])
            
            # Calculer la route alternative
            alt_route = self.route_calculator.get_route_avoiding_polygons_with_tracking(coordinates, poly)
            
            # Analyser la route alternative
            alt_tolls_dict = self.route_calculator.locate_and_cost_tolls(
                alt_route, veh_class, Config.Operations.ANALYZE_ALTERNATIVE_PERCENTAGE
            )
            alt_tolls_on_route = alt_tolls_dict["on_route"]
            
            # Calculer les métriques
            cost = sum(t.get("cost", 0) for t in alt_tolls_on_route)
            duration = alt_route["features"][0]["properties"]["summary"]["duration"]
            toll_count = len(alt_tolls_on_route)
            
            # Vérifier que le péage est bien évité
            avoided_id = str(toll["id"]).strip().lower()
            present_ids = set(str(t["id"]).strip().lower() for t in alt_tolls_on_route)
            
            if avoided_id in present_ids:
                print(f"Le péage {avoided_id} n'a pas pu être évité.")
                return None
            
            print(f"Route alternative: coût={cost}€, durée={duration/60:.1f}min")
            
            return ResultFormatter.format_route_result(alt_route, cost, duration, toll_count)
            
        except Exception as e:
            print(f"Erreur lors de l'évitement du péage {toll['id']}: {e}")
            return None
    
    def _test_toll_combinations(self, coordinates, all_tolls_sorted, price_limit, veh_class, max_comb_size, result_manager):
        """Teste des combinaisons de péages à éviter."""
        with performance_tracker.measure_operation(Config.Operations.TEST_COMBINATIONS_PERCENTAGE):
            print("Test des combinaisons de péages...")
            
            seen_combinations = set()
            
            for k in range(2, min(len(all_tolls_sorted), max_comb_size, 5) + 1):
                for to_avoid in combinations(all_tolls_sorted, k):
                    # Éviter les doublons
                    sig = tuple(sorted(t["id"] for t in to_avoid))
                    if sig in seen_combinations:
                        continue
                    seen_combinations.add(sig)                    # Heuristique d'optimisation : pré-filtrage budgétaire amélioré
                    potential_saving = sum(t.get("cost", 0) for t in to_avoid)
                    if potential_saving <= 0:
                        continue
                    
                    # Pré-filtrage rentabilité : ignorer les économies négligeables (< 5% du budget)
                    min_worthwhile_saving = price_limit * 0.05
                    if potential_saving < min_worthwhile_saving:
                        continue
                    
                    # Prioriser les combinaisons qui peuvent potentiellement résoudre le problème budgétaire
                    current_best_cost = result_manager.get_results().get("cheapest", {}).get("cost", float('inf'))
                    if current_best_cost - potential_saving > price_limit:
                        continue  # Cette combinaison ne peut pas résoudre le problème
                    
                    route_data = self._test_combination_avoidance(coordinates, to_avoid, veh_class)
                    if route_data:
                        updated = result_manager.update_with_route(route_data, float('inf'))
                        
                        # Arrêt anticipé si solution optimale trouvée
                        if updated and route_data["cost"] <= price_limit and route_data["cost"] == 0:
                            break
                
                # Arrêt anticipé si on a déjà une bonne solution
                if self._has_budget_compliant_route(result_manager, price_limit):
                    break
    
    def _test_combination_avoidance(self, coordinates, to_avoid, veh_class):
        """Teste l'évitement d'une combinaison de péages."""
        try:
            poly = avoidance_multipolygon(to_avoid)
            alt_route = self.route_calculator.get_route_avoiding_polygons_with_tracking(coordinates, poly)
            
            alt_tolls_dict = self.route_calculator.locate_and_cost_tolls(
                alt_route, veh_class, Config.Operations.ANALYZE_COMBINATION_PERCENTAGE
            )
            alt_tolls_on_route = alt_tolls_dict["on_route"]
            
            # Vérifier que les péages à éviter sont bien évités
            avoided_ids = set(str(t["id"]).strip().lower() for t in to_avoid)
            present_ids = set(str(t["id"]).strip().lower() for t in alt_tolls_on_route)
            
            if avoided_ids & present_ids:
                return None
            
            cost = sum(t.get("cost", 0) for t in alt_tolls_on_route)
            duration = alt_route["features"][0]["properties"]["summary"]["duration"]
            toll_count = len(alt_tolls_on_route)
            
            return ResultFormatter.format_route_result(alt_route, cost, duration, toll_count)
            
        except Exception:
            return None
    
    def _has_budget_compliant_route(self, result_manager, price_limit):
        """Vérifie si on a déjà une route qui respecte le budget."""
        if not result_manager.has_valid_results():
            return False
        
        results = result_manager.get_results()
        
        # CORRECTION: Vérifier que les résultats ne sont pas None
        cheapest = results.get("cheapest")
        fastest = results.get("fastest")
        
        cheapest_compliant = (cheapest and 
                            cheapest.get("route") is not None and 
                            cheapest.get("cost", float('inf')) <= price_limit)
        
        fastest_compliant = (fastest and 
                           fastest.get("route") is not None and 
                           fastest.get("cost", float('inf')) <= price_limit)
        
        return cheapest_compliant or fastest_compliant
    
    def _build_percentage_budget_result(self, result_manager, price_limit):
        """Construit le résultat final pour la contrainte de pourcentage."""
        if not result_manager.has_valid_results():
            return ResultFormatter.format_optimization_results(
                fastest=None, cheapest=None, min_tolls=None,
                status=Config.StatusCodes.NO_ROUTE_WITHIN_BUDGET
            )
        
        results = result_manager.get_results()
        fastest = results["fastest"]
        cheapest = results["cheapest"]
        min_tolls = results["min_tolls"]
        
        # CORRECTION: Vérifier que fastest n'est pas None et a une route valide
        fastest_within_budget = None
        if (fastest and 
            fastest.get("route") is not None and 
            fastest.get("cost", float('inf')) <= price_limit):
            fastest_within_budget = fastest
        
        if fastest_within_budget:
            status = Config.StatusCodes.BUDGET_SATISFIED
            print(f"Solution trouvée dans le budget: {fastest_within_budget['cost']}€ ≤ {price_limit}€")
        else:
            status = Config.StatusCodes.NO_ROUTE_WITHIN_BUDGET_RETURNING_FASTEST_AMONG_CHEAPEST
            # CORRECTION: Utiliser cheapest seulement s'il est valide
            if cheapest and cheapest.get("route") is not None:
                fastest_within_budget = cheapest
                print(f"Aucune solution dans le budget. Meilleure solution: {cheapest['cost']}€ > {price_limit}€")
            else:
                fastest_within_budget = None
                print("Aucune solution trouvée.")
        
        return ResultFormatter.format_optimization_results(
            fastest=fastest_within_budget,
            cheapest=cheapest,
            min_tolls=min_tolls,
            status=status
        )
    
    def handle_percentage_budget_route(self, coordinates, max_price_percent, veh_class=Config.DEFAULT_VEH_CLASS, max_comb_size=Config.DEFAULT_MAX_COMB_SIZE):
        """
        Point d'entrée principal pour les routes avec contrainte de pourcentage.
        
        Returns:
            dict: Résultat formaté avec fastest, cheapest, min_tolls, status
        """
        with performance_tracker.measure_operation(Config.Operations.COMPUTE_ROUTE_PERCENTAGE_BUDGET):
            return self.compute_percentage_budget_route(coordinates, max_price_percent, veh_class, max_comb_size)