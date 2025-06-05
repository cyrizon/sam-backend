"""
budget_strategies.py
------------------

Stratégies pour calculer des itinéraires avec des contraintes budgétaires.
Intègre le système de mesure des performances pour optimiser les appels.
"""

from benchmark.performance_tracker import performance_tracker
from src.services.budget.zero_budget_strategy import ZeroBudgetStrategy
from src.services.budget.percentage_budget_strategy import PercentageBudgetStrategy
from src.services.budget.absolute_budget_strategy import AbsoluteBudgetStrategy
from src.services.budget.constants import BudgetOptimizationConfig as Config
from src.services.budget.error_handler import BudgetErrorHandler
from src.services.toll.result_formatter import ResultFormatter
from itertools import combinations
from src.services.toll_locator import locate_tolls, get_all_open_tolls_by_proximity
from src.services.toll_cost import add_marginal_cost
from src.utils.poly_utils import avoidance_multipolygon


class BudgetRouteOptimizer:
    """
    Optimiseur d'itinéraires avec contraintes budgétaires.
    Intègre le tracking des performances pour analyser et optimiser les appels.
    """
    
    def __init__(self, ors_service):
        """
        Initialise l'optimiseur avec un service ORS.
        
        Args:
            ors_service: Instance de ORSService pour les appels API
        """
        self.ors = ors_service
        self.zero_budget_strategy = ZeroBudgetStrategy(ors_service)
        self.percentage_budget_strategy = PercentageBudgetStrategy(ors_service)
        self.absolute_budget_strategy = AbsoluteBudgetStrategy(ors_service)
    
    def compute_route_with_budget_limit(
        self,
        coordinates,
        max_price=None,
        max_price_percent=None,
        veh_class=Config.DEFAULT_VEH_CLASS,
        max_comb_size=Config.DEFAULT_MAX_COMB_SIZE
    ):
        """
        Calcule un itinéraire avec une contrainte de budget maximum.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            max_price: Prix maximum en euros (absolu)
            max_price_percent: Pourcentage du coût de base (0.8 = 80%)
            veh_class: Classe de véhicule pour le calcul des coûts
            max_comb_size: Limite pour les combinaisons de péages à éviter
            
        Returns:
            dict: Résultats optimisés (fastest, cheapest, min_tolls, status)
        """
        
        # Log du début de l'opération
        BudgetErrorHandler.log_operation_start(
            "compute_route_with_budget_limit",
            max_price=max_price,
            max_price_percent=max_price_percent,
            veh_class=veh_class,
            max_comb_size=max_comb_size
        )
        
        with performance_tracker.measure_operation(Config.Operations.COMPUTE_ROUTE_WITH_BUDGET_LIMIT, {
            "max_price": max_price,
            "max_price_percent": max_price_percent,
            "veh_class": veh_class,
            "max_comb_size": max_comb_size
        }):
            print(f"=== Calcul d'itinéraire avec contrainte de budget ===")
            
            try:
                # Cas spécial 1: Budget zéro ou pourcentage zéro
                if max_price == 0 or max_price_percent == 0:
                    result = self._handle_zero_budget_route(coordinates, veh_class)
                
                # Cas spécial 2: Contrainte en pourcentage
                elif max_price_percent is not None:
                    result = self._handle_percentage_budget_route(coordinates, max_price_percent, veh_class, max_comb_size)
                
                # Cas spécial 3: Contrainte absolue en euros
                elif max_price is not None:
                    result = self._handle_absolute_budget_route(coordinates, max_price, veh_class, max_comb_size)
                
                # Cas par défaut: aucune contrainte
                else:
                    result = self._handle_no_budget_constraint(coordinates, veh_class)
                
                # Log du succès
                if result and result.get("status"):
                    BudgetErrorHandler.log_operation_success(
                        "compute_route_with_budget_limit",
                        f"Status: {result['status']}"
                    )
                
                return result
                
            except Exception as e:
                BudgetErrorHandler.log_operation_failure("compute_route_with_budget_limit", str(e))
                # Re-lever l'exception pour qu'elle soit gérée au niveau supérieur
                raise
    
    def _handle_zero_budget_route(self, coordinates, veh_class):
        """Délègue à la stratégie spécialisée pour budget zéro"""
        return self.zero_budget_strategy.handle_zero_budget_route(coordinates, veh_class)
    
    def _handle_percentage_budget_route(self, coordinates, max_price_percent, veh_class, max_comb_size):
        """Délègue à la stratégie spécialisée pour budget en pourcentage"""
        return self.percentage_budget_strategy.handle_percentage_budget_route(coordinates, max_price_percent, veh_class, max_comb_size)
    
    def _handle_absolute_budget_route(self, coordinates, max_price, veh_class, max_comb_size):
        """Délègue à la stratégie spécialisée pour budget absolu"""
        return self.absolute_budget_strategy.handle_absolute_budget_route(coordinates, max_price, veh_class, max_comb_size)
    
    def _handle_no_budget_constraint(self, coordinates, veh_class):
        """
        Gère le cas où aucune contrainte de budget n'est spécifiée.
        À implémenter dans la prochaine stratégie.
        """
        print("Aucune contrainte de budget spécifiée")
        # Pour l'instant, on utilise l'ancienne logique
        return self._compute_budget_with_legacy_logic(coordinates, None, None, veh_class, Config.DEFAULT_MAX_COMB_SIZE)
    
    def _compute_budget_with_legacy_logic(self, coordinates, max_price, max_price_percent, veh_class, max_comb_size):
        """
        Logique héritée temporaire - sera remplacée par les stratégies spécialisées.
        """
        print("Recherche d'un itinéraire avec contrainte de budget...")
        
        # Cas spécial: budget de 0 euros ou 0% -> itinéraire sans péages
        if max_price == 0 or max_price_percent == 0:
            print("Budget nul ou pourcentage nul -> recherche d'un itinéraire sans péage")
            try:
                # Appel à la méthode de calcul d'itinéraire sans péages via l'API ORS
                toll_free_route = self.ors.get_route_avoid_tollways(coordinates)
                
                # Vérification qu'il n'y a vraiment pas de péage
                tolls_on_route = locate_tolls(toll_free_route, "data/barriers.csv")["on_route"]
                
                if tolls_on_route:
                    print(f"Attention: l'itinéraire sans péage contient quand même {len(tolls_on_route)} péages")
                    add_marginal_cost(tolls_on_route, veh_class)
                    cost = sum(t.get("cost", 0) for t in tolls_on_route)
                    
                    result = ResultFormatter.format_route_result(
                        toll_free_route,
                        cost,
                        toll_free_route["features"][0]["properties"]["summary"]["duration"],
                        len(tolls_on_route)
                    )
                    
                    return ResultFormatter.format_optimization_results(
                        fastest=result,
                        cheapest=result,
                        min_tolls=result,
                        status="BUDGET_ZERO_SOME_TOLLS_PRESENT"
                    )
                else:
                    result = ResultFormatter.format_route_result(
                        toll_free_route,
                        0,
                        toll_free_route["features"][0]["properties"]["summary"]["duration"],
                        0
                    )
                    
                    return ResultFormatter.format_optimization_results(
                        fastest=result,
                        cheapest=result,
                        min_tolls=result,
                        status="BUDGET_ZERO_NO_TOLL_SUCCESS"
                    )
            
            except Exception as e:
                print(f"Impossible de trouver un itinéraire sans péage: {e}")
                # On poursuit avec l'approche standard de la contrainte budgétaire en espérant trouver une solution
        
        # 1) Obtenir la route de base
        try:
            base_route = self.ors.get_base_route(coordinates)
        except Exception as e:
            print(f"Erreur lors de l'appel initial à ORS: {e}")
            return ResultFormatter.format_optimization_results(
                fastest=None,
                cheapest=None,
                min_tolls=None,
                status="ORS_CONNECTION_ERROR"
            )

        # 2) Localiser tous les péages sur et à proximité de la route
        tolls_dict = locate_tolls(base_route, "data/barriers.csv")
        tolls_on_route = tolls_dict["on_route"]
        tolls_nearby = tolls_dict["nearby"]
        print("Péages sur la route:", len(tolls_on_route))
        print("Péages proches:", len(tolls_nearby))

        # 3) Ajouter les coûts et trier par coût décroissant
        add_marginal_cost(tolls_on_route, veh_class)
        base_cost = sum(t.get("cost", 0) for t in tolls_on_route)
        base_duration = base_route["features"][0]["properties"]["summary"]["duration"]
        base_toll_count = len(tolls_on_route)
        
        # 4) Calcul du seuil de prix
        if max_price_percent is not None:
            price_limit = base_cost * max_price_percent
        elif max_price is not None:
            price_limit = max_price
        else:
            price_limit = base_cost  # par défaut, pas de contrainte
        
        print(f"Coût de base: {base_cost}€, limite de budget: {price_limit}€")
        
        # 5) Si la route de base respecte déjà le budget, on la retourne directement
        if base_cost <= price_limit:
            print("La route de base respecte déjà la contrainte de budget.")
            result = ResultFormatter.format_route_result(
                base_route,
                base_cost,
                base_duration,
                base_toll_count
            )
            
            return ResultFormatter.format_optimization_results(
                fastest=result,
                cheapest=result,
                min_tolls=result,
                status="BUDGET_ALREADY_SATISFIED"
            )
        
        # 6) Rechercher des itinéraires alternatifs
        best_cheap = ResultFormatter.format_route_result(
            base_route,
            base_cost,
            base_duration,
            base_toll_count
        )
        best_fast_within_budget = None
        
        # Limiter la recherche aux péages dans un rayon de 100km
        max_distance_m = 100000  # 100 km
        all_tolls_nearby = get_all_open_tolls_by_proximity(base_route, "data/barriers.csv", max_distance_m)
        if not all_tolls_nearby:
            all_tolls_nearby = []
        
        # Combiner les péages sur la route et à proximité
        all_tolls = tolls_on_route + tolls_nearby
        add_marginal_cost(all_tolls, veh_class)
        
        # Trier les péages par coût décroissant pour tester d'abord l'évitement des plus coûteux
        all_tolls_sorted = sorted(all_tolls, key=lambda t: t.get("cost", 0), reverse=True)
        
        # Si aucun péage n'a été trouvé, retourner la route de base
        if not all_tolls_sorted:
            print("Aucun péage trouvé, retour à la route de base.")
            result = ResultFormatter.format_route_result(
                base_route,
                base_cost,
                base_duration,
                base_toll_count
            )
            
            return ResultFormatter.format_optimization_results(
                fastest=result,
                cheapest=result,
                min_tolls=result,
                status="NO_TOLLS_FOUND"
            )
        
        seen_polygons = set()
        tested_combinations = set()
        
        # 7) D'abord tester l'évitement des péages individuellement (les plus coûteux d'abord)
        print("Test de l'évitement des péages individuels...")
        for toll in all_tolls_sorted:
            # Ne tester que les péages qui ont un coût significatif
            if toll.get("cost", 0) <= 0:
                continue
                
            print(f"Test d'évitement du péage: {toll['id']} (coût: {toll.get('cost', 0)}€)")
            
            # Créer le polygone d'évitement pour ce péage
            poly = avoidance_multipolygon([toll])
            
            try:
                alt_route = self.ors.get_route_avoiding_polygons(coordinates, poly)
            except Exception as e:
                print(f"Erreur lors de l'appel à ORS: {e}")
                continue
                
            # Vérifier les péages sur cette route alternative
            alt_tolls_dict = locate_tolls(alt_route, "data/barriers.csv")
            alt_tolls_on_route = alt_tolls_dict["on_route"]
            add_marginal_cost(alt_tolls_on_route, veh_class)
            
            # Calculer le coût total et la durée
            cost = sum(t.get("cost", 0) for t in alt_tolls_on_route)
            duration = alt_route["features"][0]["properties"]["summary"]["duration"]
            toll_count = len(alt_tolls_on_route)
            
            # Vérifier que le péage à éviter est bien évité
            avoided_id = str(toll["id"]).strip().lower()
            present_ids = set(str(t["id"]).strip().lower() for t in alt_tolls_on_route)
            
            if avoided_id in present_ids:
                print(f"Le péage {avoided_id} n'a pas pu être évité.")
                continue
                
            print(f"Route alternative: coût={cost}€, durée={duration/60:.1f}min")
            
            route_data = ResultFormatter.format_route_result(
                alt_route, 
                cost, 
                duration,
                toll_count
            )
            
            # Mettre à jour la meilleure route la moins chère
            if cost < best_cheap["cost"]:
                best_cheap = route_data
                
                # Si cette route respecte le budget, elle peut aussi être la plus rapide dans le budget
                if cost <= price_limit:
                    if best_fast_within_budget is None or duration < best_fast_within_budget["duration"]:
                        best_fast_within_budget = route_data
            
            # Mettre à jour la meilleure route qui respecte le budget
            elif cost <= price_limit:
                if best_fast_within_budget is None or duration < best_fast_within_budget["duration"]:
                    best_fast_within_budget = route_data
                    
            # Si on a trouvé une route qui ne coûte rien, inutile de continuer
            if cost == 0:
                print("Trouvé une route gratuite!")
                break
        
        # 8) Tester des combinaisons de péages si nécessaire
        if best_fast_within_budget is None:  # Aucune solution trouvée avec les péages individuels
            print("Test des combinaisons de péages...")
            for k in range(2, min(len(all_tolls_sorted), max_comb_size) + 1):
                for to_avoid in combinations(all_tolls_sorted, k):
                    # Créer une signature unique pour cette combinaison de péages
                    sig = tuple(sorted(t["id"] for t in to_avoid))
                    
                    # Éviter les combinaisons déjà testées
                    if sig in seen_polygons or sig in tested_combinations:
                        continue
                        
                    seen_polygons.add(sig)
                    tested_combinations.add(sig)
                    
                    # Vérifier si cette combinaison pourrait permettre des économies suffisantes
                    potential_saving = sum(t.get("cost", 0) for t in to_avoid)
                    if base_cost - potential_saving <= 0:
                        continue
                        
                    print(f"Test combinaison évitement: {sig}")
                    
                    # Créer l'itinéraire alternatif
                    poly = avoidance_multipolygon(to_avoid)
                    
                    try:
                        alt_route = self.ors.get_route_avoiding_polygons(coordinates, poly)
                    except Exception:
                        continue
                        
                    # Vérifier les péages sur cette route alternative
                    alt_tolls_dict = locate_tolls(alt_route, "data/barriers.csv")
                    alt_tolls_on_route = alt_tolls_dict["on_route"]
                    add_marginal_cost(alt_tolls_on_route, veh_class)
                    
                    # Calculer le coût total et la durée
                    cost = sum(t.get("cost", 0) for t in alt_tolls_on_route)
                    duration = alt_route["features"][0]["properties"]["summary"]["duration"]
                    toll_count = len(alt_tolls_on_route)
                    
                    # Vérifier que les péages à éviter sont bien évités
                    avoided_ids = set(str(t["id"]).strip().lower() for t in to_avoid)
                    present_ids = set(str(t["id"]).strip().lower() for t in alt_tolls_on_route)
                    
                    if avoided_ids & present_ids:
                        print(f"Certains péages à éviter sont toujours présents: {avoided_ids & present_ids}")
                        continue
                        
                    print(f"Route alternative: coût={cost}€, durée={duration/60:.1f}min")
                    
                    route_data = ResultFormatter.format_route_result(
                        alt_route, 
                        cost, 
                        duration,
                        toll_count
                    )
                    
                    # Mettre à jour la meilleure route la moins chère
                    if cost < best_cheap["cost"]:
                        best_cheap = route_data
                        
                        # Si cette route respecte le budget, elle peut aussi être la plus rapide dans le budget
                        if cost <= price_limit:
                            if best_fast_within_budget is None or duration < best_fast_within_budget["duration"]:
                                best_fast_within_budget = route_data
                    
                    # Mettre à jour la meilleure route qui respecte le budget
                    elif cost <= price_limit:
                        if best_fast_within_budget is None or duration < best_fast_within_budget["duration"]:
                            best_fast_within_budget = route_data
                    
                    # Si on a trouvé une route qui ne coûte rien, inutile de continuer
                    if cost == 0:
                        print("Trouvé une route gratuite!")
                        break

        # 9) Résultat final
        print(f"[RESULT] Base: coût={base_cost}€, durée={base_duration/60:.1f}min, tolls={base_toll_count}")
        print(f"[RESULT] Cheapest: coût={best_cheap['cost']}€, durée={best_cheap['duration']/60:.1f}min, tolls={best_cheap['toll_count']}")
        print(f"[RESULT] Budget maximum: {price_limit}€ {f'({max_price_percent*100}%)' if max_price_percent else ''}")
        
        # Si on n'a trouvé aucune route respectant le budget
        if best_fast_within_budget is None:
            print("Aucun itinéraire ne respecte la contrainte de budget.")
            
            # Initialiser le plus rapide des itinéraires les moins chers
            fastest_of_cheapest = best_cheap
            min_cost = best_cheap["cost"]
            
            # Ne considérer les routes alternatives (et pas la route de base) pour chercher le plus rapide
            if best_cheap["cost"] < base_cost:
                print(f"Recherche du plus rapide parmi les itinéraires les moins chers (coût min: {min_cost}€)...")
                print(f"Coût de référence: {best_cheap['cost']}€, durée: {best_cheap['duration']/60:.1f}min")
                
                # On réinitialise la recherche avec les mêmes combinaisons mais avec un nouveau critère
                seen_polygons.clear()
                tested_combinations.clear()
                
                # Deuxième passe : rechercher parmi tous les itinéraires ayant le même coût minimum 
                # celui qui est le plus rapide
                
                # Test des péages individuels d'abord
                for toll in all_tolls_sorted:
                    # Ne tester que les péages qui ont un coût significatif
                    if toll.get("cost", 0) <= 0:
                        continue
                    
                    # Créer le polygone d'évitement pour ce péage
                    poly = avoidance_multipolygon([toll])
                    
                    try:
                        alt_route = self.ors.get_route_avoiding_polygons(coordinates, poly)
                    except Exception:
                        continue
                    
                    # Vérifier les péages sur cette route alternative
                    alt_tolls_dict = locate_tolls(alt_route, "data/barriers.csv")
                    alt_tolls_on_route = alt_tolls_dict["on_route"]
                    add_marginal_cost(alt_tolls_on_route, veh_class)
                    
                    # Calculer le coût total et la durée
                    cost = sum(t.get("cost", 0) for t in alt_tolls_on_route)
                    duration = alt_route["features"][0]["properties"]["summary"]["duration"]
                    toll_count = len(alt_tolls_on_route)
                    
                    # Si c'est une route qui a le même coût que la moins chère et est plus rapide
                    if abs(cost - min_cost) < 0.01 and duration < fastest_of_cheapest["duration"]:
                        print(f"Trouvé un itinéraire plus rapide avec le même coût minimal: {duration/60:.1f}min vs {fastest_of_cheapest['duration']/60:.1f}min")
                        fastest_of_cheapest = ResultFormatter.format_route_result(
                            alt_route,
                            cost,
                            duration,
                            toll_count
                        )
                
                # Test des combinaisons de péages ensuite
                for k in range(2, min(len(all_tolls_sorted), max_comb_size) + 1):
                    for to_avoid in combinations(all_tolls_sorted, k):
                        # Créer une signature unique pour cette combinaison de péages
                        sig = tuple(sorted(t["id"] for t in to_avoid))
                        
                        # Éviter les combinaisons déjà testées
                        if sig in seen_polygons or sig in tested_combinations:
                            continue
                        
                        seen_polygons.add(sig)
                        tested_combinations.add(sig)
                        
                        # Vérifier si cette combinaison pourrait permettre des économies suffisantes
                        potential_saving = sum(t.get("cost", 0) for t in to_avoid)
                        if base_cost - potential_saving <= 0:
                            continue
                        
                        # Créer l'itinéraire alternatif
                        poly = avoidance_multipolygon(to_avoid)
                        
                        try:
                            alt_route = self.ors.get_route_avoiding_polygons(coordinates, poly)
                        except Exception:
                            continue
                        
                        # Vérifier les péages sur cette route alternative
                        alt_tolls_dict = locate_tolls(alt_route, "data/barriers.csv")
                        alt_tolls_on_route = alt_tolls_dict["on_route"]
                        add_marginal_cost(alt_tolls_on_route, veh_class)
                        
                        # Calculer le coût total et la durée
                        cost = sum(t.get("cost", 0) for t in alt_tolls_on_route)
                        duration = alt_route["features"][0]["properties"]["summary"]["duration"]
                        toll_count = len(alt_tolls_on_route)
                        
                        # Si c'est une route qui a le même coût que la moins chère et est plus rapide
                        if abs(cost - min_cost) < 0.01 and duration < fastest_of_cheapest["duration"]:
                            print(f"Trouvé un itinéraire plus rapide avec le même coût minimal: {duration/60:.1f}min vs {fastest_of_cheapest['duration']/60:.1f}min")
                            fastest_of_cheapest = ResultFormatter.format_route_result(
                                alt_route,
                                cost,
                                duration,
                                toll_count
                            )
                
                print(f"[RESULT] Fastest of cheapest: coût={fastest_of_cheapest['cost']}€, "
                      f"durée={fastest_of_cheapest['duration']/60:.1f}min, tolls={fastest_of_cheapest['toll_count']}")
                
                # On retourne le plus rapide des moins chers comme solution la plus rapide
                best_fast_within_budget = fastest_of_cheapest
                status = "NO_ROUTE_WITHIN_BUDGET_RETURNING_FASTEST_AMONG_CHEAPEST"
            else:
                # Si on n'a pas trouvé d'itinéraire moins cher que la base, on retourne la route la moins chère
                best_fast_within_budget = best_cheap
                status = "NO_ROUTE_WITHIN_BUDGET"
        else:
            print(f"[RESULT] Fastest within budget: coût={best_fast_within_budget['cost']}€, "
                  f"durée={best_fast_within_budget['duration']/60:.1f}min, tolls={best_fast_within_budget['toll_count']}")
            status = "BUDGET_SATISFIED"
        
        return ResultFormatter.format_optimization_results(
            fastest=best_fast_within_budget or best_cheap,
            cheapest=best_cheap,
            min_tolls=best_cheap,  # Pour l'instant, même que cheapest
            status=status if 'status' in locals() else ("BUDGET_SATISFIED" if best_fast_within_budget else "NO_ROUTE_WITHIN_BUDGET")
        )
