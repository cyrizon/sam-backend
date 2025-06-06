"""
fallback_strategy.py
-------------------

Stratégie de fallback pour gérer les cas où aucune solution ne respecte le budget.
Responsabilité unique : fournir des alternatives intelligentes quand les contraintes ne peuvent être respectées.
"""

from benchmark.performance_tracker import performance_tracker
from src.services.budget.constants import BudgetOptimizationConfig as Config
from src.services.common.result_formatter import ResultFormatter
from src.services.budget.result_manager import BudgetRouteResultManager as RouteResultManager
from src.services.budget.route_calculator import BudgetRouteCalculator as RouteCalculator
from src.services.budget.error_handler import BudgetErrorHandler
from src.services.ors_config_manager import ORSConfigManager
from src.services.toll_locator import locate_tolls, get_all_open_tolls_by_proximity
from src.services.toll_cost import add_marginal_cost
from src.utils.poly_utils import avoidance_multipolygon
from itertools import combinations


class BudgetFallbackStrategy:
    """
    Stratégie de fallback pour l'optimisation budgétaire.
    Fournit des alternatives intelligentes quand les contraintes ne peuvent être respectées.
    """
    
    def __init__(self, ors_service):
        """
        Initialise la stratégie avec un service ORS.
        
        Args:
            ors_service: Instance de ORSService pour les appels API
        """
        self.ors = ors_service
        self.route_calculator = RouteCalculator(ors_service)
    
    def handle_budget_failure(self, coordinates, budget_limit, budget_type, veh_class=Config.DEFAULT_VEH_CLASS, max_comb_size=Config.DEFAULT_MAX_COMB_SIZE):
        """
        Gère l'échec de respecter une contrainte budgétaire en proposant des alternatives.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            budget_limit: Limite budgétaire originale
            budget_type: Type de budget ("zero", "absolute", "percentage", "none")
            veh_class: Classe de véhicule
            max_comb_size: Limite pour les combinaisons de péages à éviter
            
        Returns:
            dict: Résultat de fallback formaté
        """
        # Validation précoce des coordonnées
        try:
            ORSConfigManager.validate_coordinates(coordinates)
        except ValueError as e:
            return BudgetErrorHandler.handle_ors_error(e, "validation_coordinates")
        
        with performance_tracker.measure_operation(Config.Operations.HANDLE_BUDGET_FAILURE):
            print(f"=== Stratégie de fallback pour budget {budget_type} ===")
            
            try:
                # Stratégies de fallback selon le type de contrainte
                if budget_type == "zero":
                    return self._handle_zero_budget_fallback(coordinates, veh_class, max_comb_size)
                elif budget_type == "absolute":
                    return self._handle_absolute_budget_fallback(coordinates, budget_limit, veh_class, max_comb_size)
                elif budget_type == "percentage":
                    return self._handle_percentage_budget_fallback(coordinates, budget_limit, veh_class, max_comb_size)
                else:
                    return self._handle_general_fallback(coordinates, veh_class, max_comb_size)
                    
            except Exception as e:
                print(f"Erreur lors du fallback budgétaire: {e}")
                return BudgetErrorHandler.handle_ors_error(e, Config.Operations.HANDLE_BUDGET_FAILURE)
    
    def _handle_zero_budget_fallback(self, coordinates, veh_class, max_comb_size):
        """Fallback spécialisé pour les budgets zéro."""
        with performance_tracker.measure_operation(Config.Operations.ZERO_BUDGET_FALLBACK):
            print("Fallback budget zéro : recherche d'alternatives gratuites ou peu chères...")
            
            # 1) Rechercher d'abord des routes complètement gratuites
            free_route = self._search_for_free_routes(coordinates, veh_class, max_comb_size)
            if free_route:
                print("Route gratuite trouvée en fallback !")
                return ResultFormatter.format_uniform_result(
                    free_route, Config.StatusCodes.FREE_ALTERNATIVE_FOUND
                )
            
            # 2) Si pas de route gratuite, trouver la moins chère possible
            cheapest_route = self._find_absolute_cheapest(coordinates, veh_class, max_comb_size)
            if cheapest_route:
                print(f"Route la moins chère trouvée: {cheapest_route['cost']}€")
                return ResultFormatter.format_uniform_result(
                    cheapest_route, Config.StatusCodes.ONLY_CHEAPEST_FOUND
                )
            
            # 3) Fallback ultime: route de base
            return self._get_base_route_fallback(coordinates, veh_class)
    
    def _handle_absolute_budget_fallback(self, coordinates, budget_limit, veh_class, max_comb_size):
        """Fallback spécialisé pour les budgets absolus."""
        with performance_tracker.measure_operation(Config.Operations.ABSOLUTE_BUDGET_FALLBACK):
            print(f"Fallback budget absolu : recherche d'alternatives proches de {budget_limit}€...")
            
            # 1) Rechercher la solution la plus proche du budget
            closest_route = self._find_closest_to_budget(coordinates, budget_limit, veh_class, max_comb_size)
            if closest_route:
                cost_diff = abs(closest_route['cost'] - budget_limit)
                print(f"Route la plus proche du budget trouvée: {closest_route['cost']}€ (écart: {cost_diff}€)")
                
                # Si l'écart est raisonnable (< 20% du budget), c'est acceptable
                if cost_diff <= budget_limit * 0.2:
                    return ResultFormatter.format_uniform_result(
                        closest_route, Config.StatusCodes.CLOSEST_TO_BUDGET_FOUND
                    )
            
            # 2) Sinon, trouver la route la moins chère
            return self._fallback_to_cheapest(coordinates, veh_class, max_comb_size)
    
    def _handle_percentage_budget_fallback(self, coordinates, budget_limit, veh_class, max_comb_size):
        """Fallback spécialisé pour les budgets en pourcentage."""
        with performance_tracker.measure_operation(Config.Operations.PERCENTAGE_BUDGET_FALLBACK):
            print(f"Fallback budget pourcentage : recherche d'alternatives pour {budget_limit*100}%...")
            
            # Pour le pourcentage, on essaie d'augmenter progressivement le seuil
            expanded_percentages = [budget_limit * 1.1, budget_limit * 1.25, budget_limit * 1.5]
            
            for expanded_pct in expanded_percentages:
                print(f"Tentative avec seuil élargi: {expanded_pct*100}%")
                expanded_route = self._find_route_within_percentage(coordinates, expanded_pct, veh_class, max_comb_size)
                if expanded_route:
                    print(f"Solution trouvée avec seuil élargi de {expanded_pct*100}%")
                    return ResultFormatter.format_uniform_result(
                        expanded_route, Config.StatusCodes.EXPANDED_BUDGET_SATISFIED
                    )
            
            # Fallback vers la route la moins chère
            return self._fallback_to_cheapest(coordinates, veh_class, max_comb_size)
    
    def _handle_general_fallback(self, coordinates, veh_class, max_comb_size):
        """Fallback général quand aucune contrainte spécifique."""
        with performance_tracker.measure_operation(Config.Operations.GENERAL_FALLBACK):
            print("Fallback général : recherche de la meilleure solution globale...")
            
            return self.find_fastest_among_cheapest(coordinates, veh_class, max_comb_size)
    
    def _search_for_free_routes(self, coordinates, veh_class, max_comb_size, max_attempts=10):
        """Recherche intensive de routes complètement gratuites."""
        with performance_tracker.measure_operation(Config.Operations.SEARCH_FREE_ROUTES):
            
            # 1) Essayer d'abord la route avoid_tollways
            try:
                toll_free_route = self.route_calculator.get_route_avoid_tollways_with_tracking(coordinates)
                tolls_dict = self.route_calculator.locate_and_cost_tolls(toll_free_route, veh_class)
                
                if not tolls_dict["on_route"]:  # Vraiment aucun péage
                    return ResultFormatter.format_route_result(
                        toll_free_route, 0, 
                        toll_free_route["features"][0]["properties"]["summary"]["duration"], 
                        0
                    )
            except Exception:
                pass
            
            # 2) Recherche par évitement de péages
            base_route = self.route_calculator.get_base_route_with_tracking(coordinates)
            tolls_dict = locate_tolls(base_route, Config.get_barriers_csv_path())
            all_tolls = tolls_dict["on_route"] + tolls_dict["nearby"]
            add_marginal_cost(all_tolls, veh_class)
            
            # Tester l'évitement de différentes combinaisons
            attempts = 0
            for k in range(1, min(len(all_tolls), max_comb_size) + 1):
                if attempts >= max_attempts:
                    break
                    
                for to_avoid in combinations(all_tolls, k):
                    if attempts >= max_attempts:
                        break
                        
                    attempts += 1
                    route_data = self._test_combination_for_free_route(coordinates, to_avoid, veh_class)
                    if route_data and route_data["cost"] == 0:
                        return route_data
            
            return None
    
    def _test_combination_for_free_route(self, coordinates, to_avoid, veh_class):
        """Teste une combinaison spécifique pour obtenir une route gratuite."""
        try:
            poly = avoidance_multipolygon(to_avoid)
            alt_route = self.route_calculator.get_route_avoiding_polygons_with_tracking(coordinates, poly)
            
            alt_tolls_dict = self.route_calculator.locate_and_cost_tolls(alt_route, veh_class)
            alt_tolls_on_route = alt_tolls_dict["on_route"]
            
            cost = sum(t.get("cost", 0) for t in alt_tolls_on_route)
            
            if cost == 0:  # Route gratuite trouvée !
                duration = alt_route["features"][0]["properties"]["summary"]["duration"]
                return ResultFormatter.format_route_result(alt_route, 0, duration, 0)
                
        except Exception:
            pass
        
        return None
    
    def _find_absolute_cheapest(self, coordinates, veh_class, max_comb_size):
        """Trouve la route absolument la moins chère possible."""
        with performance_tracker.measure_operation(Config.Operations.FIND_ABSOLUTE_CHEAPEST):
            
            result_manager = RouteResultManager()
            
            # Route de base comme référence
            base_route = self.route_calculator.get_base_route_with_tracking(coordinates)
            base_metrics = self._get_route_metrics(base_route, veh_class)
            result_manager.update_with_route(base_metrics, float('inf'))
            
            # Tester toutes les combinaisons possibles pour trouver le minimum absolu
            tolls_dict = locate_tolls(base_route, Config.get_barriers_csv_path())
            all_tolls = tolls_dict["on_route"] + tolls_dict["nearby"]
            add_marginal_cost(all_tolls, veh_class)
            
            # Recherche exhaustive des combinaisons les plus prometteuses
            for k in range(1, min(len(all_tolls), max_comb_size) + 1):
                for to_avoid in combinations(all_tolls, k):
                    route_data = self._test_combination_avoidance_simple(coordinates, to_avoid, veh_class)
                    if route_data:
                        result_manager.update_with_route(route_data, float('inf'))
            
            results = result_manager.get_results()
            return results.get("cheapest")
    
    def _find_closest_to_budget(self, coordinates, budget_limit, veh_class, max_comb_size):
        """Trouve la route la plus proche du budget donné."""
        with performance_tracker.measure_operation(Config.Operations.FIND_CLOSEST_TO_BUDGET):
            
            best_route = None
            best_distance = float('inf')
            
            # Route de base
            base_route = self.route_calculator.get_base_route_with_tracking(coordinates)
            base_metrics = self._get_route_metrics(base_route, veh_class)
            base_distance = abs(base_metrics["cost"] - budget_limit)
            
            if base_distance < best_distance:
                best_distance = base_distance
                best_route = base_metrics
            
            # Tester des alternatives
            tolls_dict = locate_tolls(base_route, Config.get_barriers_csv_path())
            all_tolls = tolls_dict["on_route"] + tolls_dict["nearby"]
            add_marginal_cost(all_tolls, veh_class)
            
            for k in range(1, min(len(all_tolls), max_comb_size) + 1):
                for to_avoid in combinations(all_tolls, k):
                    route_data = self._test_combination_avoidance_simple(coordinates, to_avoid, veh_class)
                    if route_data:
                        distance = abs(route_data["cost"] - budget_limit)
                        if distance < best_distance:
                            best_distance = distance
                            best_route = route_data
            
            return best_route
    
    def _find_route_within_percentage(self, coordinates, percentage_limit, veh_class, max_comb_size):
        """Trouve une route respectant un pourcentage élargi."""
        base_route = self.route_calculator.get_base_route_with_tracking(coordinates)
        base_metrics = self._get_route_metrics(base_route, veh_class)
        base_cost = base_metrics["cost"]
        price_limit = base_cost * percentage_limit
        
        if base_cost <= price_limit:
            return base_metrics
        
        # Rechercher des alternatives
        tolls_dict = locate_tolls(base_route, Config.get_barriers_csv_path())
        all_tolls = tolls_dict["on_route"] + tolls_dict["nearby"]
        add_marginal_cost(all_tolls, veh_class)
        
        for k in range(1, min(len(all_tolls), max_comb_size) + 1):
            for to_avoid in combinations(all_tolls, k):
                route_data = self._test_combination_avoidance_simple(coordinates, to_avoid, veh_class)
                if route_data and route_data["cost"] <= price_limit:
                    return route_data
        
        return None
    
    def _fallback_to_cheapest(self, coordinates, veh_class, max_comb_size):
        """Fallback vers la route la moins chère."""
        cheapest_route = self._find_absolute_cheapest(coordinates, veh_class, max_comb_size)
        if cheapest_route:
            return ResultFormatter.format_uniform_result(
                cheapest_route, Config.StatusCodes.ONLY_CHEAPEST_FOUND
            )
        
        return self._get_base_route_fallback(coordinates, veh_class)
    
    def _get_base_route_fallback(self, coordinates, veh_class):
        """Fallback ultime avec la route de base."""
        try:
            base_route = self.route_calculator.get_base_route_with_tracking(coordinates)
            base_metrics = self._get_route_metrics(base_route, veh_class)
            
            return ResultFormatter.format_uniform_result(
                base_metrics, Config.StatusCodes.FALLBACK_BASE_ROUTE_USED
            )
        except Exception as e:
            return BudgetErrorHandler.handle_ors_error(e, Config.Operations.GET_BASE_ROUTE_FALLBACK)
    
    def _test_combination_avoidance_simple(self, coordinates, to_avoid, veh_class):
        """Version simplifiée du test d'évitement pour le fallback."""
        try:
            poly = avoidance_multipolygon(to_avoid)
            alt_route = self.route_calculator.get_route_avoiding_polygons_with_tracking(coordinates, poly)
            return self._get_route_metrics(alt_route, veh_class)
        except Exception:
            return None
    
    def _get_route_metrics(self, route, veh_class):
        """Calcule les métriques d'une route."""
        tolls_dict = self.route_calculator.locate_and_cost_tolls(route, veh_class)
        tolls_on_route = tolls_dict["on_route"]
        
        cost = sum(t.get("cost", 0) for t in tolls_on_route)
        duration = route["features"][0]["properties"]["summary"]["duration"]
        toll_count = len(tolls_on_route)
        
        return ResultFormatter.format_route_result(route, cost, duration, toll_count)
    
    def find_fastest_among_cheapest(self, coordinates, veh_class=Config.DEFAULT_VEH_CLASS, max_comb_size=Config.DEFAULT_MAX_COMB_SIZE):
        """
        Trouve la route la plus rapide parmi les routes les moins chères.
        Version optimisée pour le fallback général.
        
        Returns:
            dict: Résultat formaté avec fastest, cheapest, min_tolls, status
        """
        with performance_tracker.measure_operation(Config.Operations.FIND_FASTEST_AMONG_CHEAPEST):
            print("Recherche du plus rapide parmi les routes les moins chères...")
            
            try:
                result_manager = RouteResultManager()
                
                # Route de base
                base_route = self.route_calculator.get_base_route_with_tracking(coordinates)
                base_metrics = self._get_route_metrics(base_route, veh_class)
                result_manager.update_with_route(base_metrics, float('inf'))
                
                # Recherche d'alternatives
                tolls_dict = locate_tolls(base_route, Config.get_barriers_csv_path())
                all_tolls = tolls_dict["on_route"] + tolls_dict["nearby"]
                add_marginal_cost(all_tolls, veh_class)
                
                # Limiter le nombre de combinaisons pour éviter les timeouts
                max_combinations = Config.MAX_FALLBACK_COMBINATIONS
                tested = 0
                
                for k in range(1, min(len(all_tolls), max_comb_size) + 1):
                    if tested >= max_combinations:
                        break
                        
                    for to_avoid in combinations(all_tolls, k):
                        if tested >= max_combinations:
                            break
                            
                        tested += 1
                        route_data = self._test_combination_avoidance_simple(coordinates, to_avoid, veh_class)
                        if route_data:
                            result_manager.update_with_route(route_data, float('inf'))
                
                # Construire le résultat final
                results = result_manager.get_results()
                
                if results["cheapest"]:
                    return ResultFormatter.format_optimization_results(
                        fastest=results["fastest"],
                        cheapest=results["cheapest"],
                        min_tolls=results["min_tolls"],
                        status=Config.StatusCodes.FASTEST_AMONG_CHEAPEST_FOUND
                    )
                else:
                    return ResultFormatter.format_optimization_results(
                        fastest=None, cheapest=None, min_tolls=None,
                        status=Config.StatusCodes.NO_ALTERNATIVE_FOUND
                    )
                    
            except Exception as e:
                print(f"Erreur lors de la recherche fastest among cheapest: {e}")
                return self._get_base_route_fallback(coordinates, veh_class)