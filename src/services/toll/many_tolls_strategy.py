"""
many_tolls_strategy.py
---------------------

Stratégie pour calculer des itinéraires avec plusieurs péages autorisés.
Responsabilité unique : optimiser les routes en testant des combinaisons de péages à éviter.
"""

from itertools import combinations
from src.services.toll_locator import locate_tolls
from src.services.toll_cost import add_marginal_cost
from src.utils.poly_utils import avoidance_multipolygon
from src.utils.route_utils import format_route_result
from benchmark.performance_tracker import performance_tracker


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
                return self._create_base_route_result(base_route)

            # Initialisation des métriques de base
            base_result = self._initialize_base_metrics(base_route, veh_class, max_tolls)
            best_cheap = base_result["best_cheap"]
            best_fast = base_result["best_fast"]
            best_min_tolls = base_result["best_min_tolls"]
            base_cost = base_result["base_cost"]

            # Génération et test des combinaisons
            combination_results = self._test_toll_combinations(
                coordinates, all_tolls_sorted, max_tolls, veh_class, max_comb_size, 
                base_cost, best_cheap, best_fast, best_min_tolls
            )
            
            best_cheap = combination_results["best_cheap"]
            best_fast = combination_results["best_fast"]
            best_min_tolls = combination_results["best_min_tolls"]

            # Fallback si rien trouvé
            fallback_result = self._apply_fallback_if_needed(
                base_route, veh_class, max_tolls, best_fast, best_cheap, best_min_tolls
            )
            
            best_cheap = fallback_result["best_cheap"]
            best_fast = fallback_result["best_fast"]
            best_min_tolls = fallback_result["best_min_tolls"]

            # Affichage des résultats et validation finale
            self._log_final_results(best_cheap, best_fast, best_min_tolls, base_result["base_toll_count"], base_result["base_cost"], base_result["base_duration"])

            # Si aucune solution trouvée, retourner None
            if not (best_fast["route"] or best_cheap["route"] or best_min_tolls["route"]):
                print("Aucun itinéraire trouvé respectant la contrainte de max_tolls")
                return None
                
            # Formater les résultats avec structure complète
            return {
                "fastest": best_fast,
                "cheapest": best_cheap,
                "min_tolls": best_min_tolls
            }
    
    def _create_base_route_result(self, base_route):
        """Crée un résultat avec la route de base quand aucun péage n'est trouvé."""
        return {
            "fastest": format_route_result(base_route, 0, base_route["features"][0]["properties"]["summary"]["duration"], 0),
            "cheapest": format_route_result(base_route, 0, base_route["features"][0]["properties"]["summary"]["duration"], 0),
            "min_tolls": format_route_result(base_route, 0, base_route["features"][0]["properties"]["summary"]["duration"], 0)
        }
    
    def _initialize_base_metrics(self, base_route, veh_class, max_tolls):
        """Initialise les métriques de base pour la comparaison."""
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
            
            return {
                "best_cheap": best_cheap,
                "best_fast": best_fast,
                "best_min_tolls": best_min_tolls,
                "base_cost": base_cost,
                "base_duration": base_duration,
                "base_toll_count": base_toll_count
            }
    
    def _test_toll_combinations(self, coordinates, all_tolls_sorted, max_tolls, veh_class, max_comb_size, 
                              base_cost, best_cheap, best_fast, best_min_tolls):
        """Teste toutes les combinaisons de péages à éviter."""
        with performance_tracker.measure_operation("test_toll_combinations"):
            seen_polygons = set()
            tested_combinations = set()
            combination_count = 0
            
            for k in range(1, min(len(all_tolls_sorted), max_comb_size) + 1):
                for to_avoid in combinations(all_tolls_sorted, k):
                    combination_count += 1
                    
                    # Affichage périodique des stats
                    if combination_count % 10 == 0:  # Tous les 10 tests
                        stats = performance_tracker.get_current_stats()
                        print(f"Progression: {combination_count} combinaisons testées")
                    
                    result = self._test_single_combination(
                        coordinates, to_avoid, max_tolls, veh_class, combination_count, k,
                        seen_polygons, tested_combinations, base_cost, best_cheap, best_fast, best_min_tolls
                    )
                    
                    if result:
                        best_cheap = result["best_cheap"]
                        best_fast = result["best_fast"]
                        best_min_tolls = result["best_min_tolls"]
                        
                        # Arrêt anticipé si coût nul
                        if best_cheap["cost"] == 0:
                            break
            
            return {
                "best_cheap": best_cheap,
                "best_fast": best_fast,
                "best_min_tolls": best_min_tolls
            }
    
    def _test_single_combination(self, coordinates, to_avoid, max_tolls, veh_class, combination_count, k,
                               seen_polygons, tested_combinations, base_cost, best_cheap, best_fast, best_min_tolls):
        """Teste une combinaison spécifique de péages à éviter."""
        with performance_tracker.measure_operation("test_single_combination", {
            "combination_size": k,
            "combination_count": combination_count
        }):
            sig = tuple(sorted(t["id"] for t in to_avoid))
            if sig in seen_polygons:
                return None
            seen_polygons.add(sig)

            # Heuristique : coût potentiel économisé
            potential_saving = sum(t.get("cost", 0) for t in to_avoid)
            # Si l'économie potentielle ne permet pas de passer sous le coût de base, on skip
            if base_cost - potential_saving <= 0:
                return None
            # Caching/mémorisation
            if sig in tested_combinations:
                return None
            tested_combinations.add(sig)

            with performance_tracker.measure_operation("create_avoidance_polygon"):
                poly = avoidance_multipolygon(to_avoid)
            
            try:
                with performance_tracker.measure_operation("ORS_alternative_route"):
                    performance_tracker.count_api_call("ORS_alternative_route")
                    alt_route = self.ors.get_route_avoiding_polygons(coordinates, poly)
            except Exception:
                return None  # ORS n'a pas trouvé d'itinéraire

            return self._analyze_alternative_route(
                alt_route, to_avoid, max_tolls, veh_class, base_cost, best_cheap, best_fast, best_min_tolls
            )
    
    def _analyze_alternative_route(self, alt_route, to_avoid, max_tolls, veh_class, base_cost, 
                                 best_cheap, best_fast, best_min_tolls):
        """Analyse un itinéraire alternatif et met à jour les meilleures solutions."""
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
                return None  # On ignore cet itinéraire

            # Contrainte : respecter max_tolls
            if toll_count > max_tolls:
                print(f"Itinéraire ignoré : {toll_count} péages > max_tolls={max_tolls}")
                return None
                
            # Création du dictionnaire pour cet itinéraire
            route_data = format_route_result(alt_route, cost, duration, toll_count)

            # Mise à jour des meilleures solutions
            updated_best_cheap = best_cheap
            updated_best_fast = best_fast
            updated_best_min_tolls = best_min_tolls

            # Mise à jour de l'itinéraire avec le moins de péages
            if toll_count < best_min_tolls["toll_count"]:
                updated_best_min_tolls = route_data

            # Si l'itinéraire est moins cher que le best_cheap actuel
            if cost < best_cheap["cost"]:
                updated_best_cheap = route_data
                # Si best_fast n'est pas encore défini ou si cet itinéraire est plus rapide et respecte le budget
                if best_fast["route"] is None or duration < best_fast["duration"]:
                    updated_best_fast = route_data
            
            # Pour le plus rapide : on ne retient que les itinéraires dont le coût <= coût de base
            if cost <= base_cost:
                if best_fast["route"] is None or duration < best_fast["duration"]:
                    updated_best_fast = route_data

            return {
                "best_cheap": updated_best_cheap,
                "best_fast": updated_best_fast,
                "best_min_tolls": updated_best_min_tolls
            }
    
    def _apply_fallback_if_needed(self, base_route, veh_class, max_tolls, best_fast, best_cheap, best_min_tolls):
        """Applique la route de base comme fallback si nécessaire."""
        base_tolls = locate_tolls(base_route, "data/barriers.csv")["on_route"]
        add_marginal_cost(base_tolls, veh_class)
        base_cost = sum(t.get("cost", 0) for t in base_tolls)
        base_duration = base_route["features"][0]["properties"]["summary"]["duration"]
        base_toll_count = len(base_tolls)
        
        updated_best_fast = best_fast
        updated_best_cheap = best_cheap
        updated_best_min_tolls = best_min_tolls
        
        # Fallback si rien trouvé (mais seulement si base_toll_count <= max_tolls)
        if best_fast["route"] is None and base_toll_count <= max_tolls:
            updated_best_fast = format_route_result(base_route, base_cost, base_duration, base_toll_count)
            
        if best_cheap["route"] is None and base_toll_count <= max_tolls:
            updated_best_cheap = format_route_result(base_route, base_cost, base_duration, base_toll_count)
            
        if best_min_tolls["route"] is None and base_toll_count <= max_tolls:
            updated_best_min_tolls = format_route_result(base_route, base_cost, base_duration, base_toll_count)
        
        return {
            "best_fast": updated_best_fast,
            "best_cheap": updated_best_cheap,
            "best_min_tolls": updated_best_min_tolls
        }
    
    def _log_final_results(self, best_cheap, best_fast, best_min_tolls, base_toll_count, base_cost, base_duration):
        """Affiche les résultats finaux."""
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