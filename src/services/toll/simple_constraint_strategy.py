"""
simple_constraint_strategy.py
----------------------------

Stratégie simplifiée pour respecter les contraintes de péages.
Objectif : 
1. Trouver une route avec ≤ max_tolls péages (priorité 1)
2. Si pas trouvé, essayer max_tolls + 1 péages (priorité 2) 
3. Si toujours rien, fallback (priorité 3)

Pas d'optimisation de coût, juste respect des contraintes.
"""

from benchmark.performance_tracker import performance_tracker
from src.services.toll.route_calculator import RouteCalculator
from src.services.toll.constants import TollOptimizationConfig as Config
from src.services.toll.error_handler import TollErrorHandler
from src.services.common.result_formatter import ResultFormatter
from src.services.common.toll_messages import TollMessages
from src.services.ors_config_manager import ORSConfigManager


class SimpleConstraintStrategy:
    """
    Stratégie simplifiée pour respecter les contraintes de péages.
    Approche pragmatique avec backup max_tolls + 1.
    """
    
    def __init__(self, ors_service):
        self.ors = ors_service
        self.route_calculator = RouteCalculator(ors_service)
    
    def find_route_respecting_constraint(self, coordinates, max_tolls, veh_class=Config.DEFAULT_VEH_CLASS):
        """
        Trouve une route respectant la contrainte de péages avec priorisation intelligente.
        
        Nouvelle logique de priorité :
        1. Route avec exactement max_tolls péages (priorité 1)
        2. Route avec max_tolls + 1 péages (priorité 2) 
        3. Route avec max_tolls - 1 péages (priorité 3)
        4. Route sans péage (priorité 4)
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            max_tolls: Nombre maximum de péages autorisés
            veh_class: Classe de véhicule pour le calcul des coûts
            
        Returns:
            dict: {
                "primary_route": meilleure_route_trouvée,
                "backup_route": route_alternative ou None,
                "found_solution": "exact" | "plus_one" | "minus_one" | "no_toll" | "none"
            }
        """
        # Validation précoce des coordonnées
        try:
            ORSConfigManager.validate_coordinates(coordinates)
        except ValueError as e:
            return TollErrorHandler.handle_ors_error(e, "validation_coordinates")
        
        with performance_tracker.measure_operation("simple_constraint_strategy", {
            "max_tolls": max_tolls
        }):
            print(f"=== Recherche route optimale pour {max_tolls} péages (priorité exacte) ===")
            # Cas spécial : aucun péage autorisé
            if max_tolls == 0:
                return self._handle_no_toll_case(coordinates, veh_class)
            
            # Recherche séquentielle : s'arrêter dès qu'une solution est trouvée
            
            # 1. Priorité 1: Exactement max_tolls péages
            print(f"🎯 Recherche priorité 1: exactement {max_tolls} péages...")
            exact_route = self._find_route_with_exact_tolls(coordinates, max_tolls, veh_class)
            if exact_route:
                print(f"✅ Solution EXACTE trouvée: {exact_route['toll_count']} péages (= {max_tolls})")
                return {
                    "primary_route": exact_route,
                    "backup_route": None,
                    "found_solution": "exact"
                }
            
            # 2. Priorité 2: max_tolls + 1 péages
            print(f"🔄 Recherche priorité 2: {max_tolls + 1} péages...")
            plus_one_route = self._find_route_with_exact_tolls(coordinates, max_tolls + 1, veh_class)
            if plus_one_route:
                print(f"✅ Solution +1 trouvée: {plus_one_route['toll_count']} péages (= {max_tolls + 1})")
                return {
                    "primary_route": plus_one_route,
                    "backup_route": None,
                    "found_solution": "plus_one"
                }
            
            # 3. Priorité 3: max_tolls - 1 péages (sauf si max_tolls = 1)
            if max_tolls > 1:
                print(f"📉 Recherche priorité 3: {max_tolls - 1} péages...")
                minus_one_route = self._find_route_with_exact_tolls(coordinates, max_tolls - 1, veh_class)
                if minus_one_route:
                    print(f"✅ Solution -1 trouvée: {minus_one_route['toll_count']} péages (= {max_tolls - 1})")
                    return {
                        "primary_route": minus_one_route,
                        "backup_route": None,
                        "found_solution": "minus_one"
                    }
            
            # 4. Priorité 4: Route sans péage (dernier recours)
            print(f"🚫 Recherche priorité 4: route sans péage...")
            no_toll_route = self._find_route_with_exact_tolls(coordinates, 0, veh_class)
            if no_toll_route:
                print(f"✅ Solution sans péage trouvée: {no_toll_route['toll_count']} péages")
                return {
                    "primary_route": no_toll_route,
                    "backup_route": None,
                    "found_solution": "no_toll"
                }
            
            # Aucune solution trouvée
            print("❌ Aucune solution trouvée dans toutes les priorités")
            return {
                "primary_route": None,
                "backup_route": None,
                "found_solution": "none"
            }
    
    def _handle_no_toll_case(self, coordinates, veh_class):
        """Gère le cas spécial max_tolls = 0."""
        print(TollMessages.SEARCH_NO_TOLL)
        
        try:
            toll_free_route = self.route_calculator.get_route_avoid_tollways_with_tracking(coordinates)
            # Vérifier s'il reste des péages
            tolls_dict = self.route_calculator.locate_and_cost_tolls(
                toll_free_route, veh_class, "locate_tolls_no_toll"
            )
            tolls_on_route = tolls_dict["on_route"]
            toll_count = len(tolls_on_route)
            
            if toll_count == 0:
                print("✅ Route sans péage trouvée")
                route_result = ResultFormatter.format_route_result(
                    toll_free_route, 0,
                    toll_free_route["features"][0]["properties"]["summary"]["duration"], 0
                )
                return {
                    "primary_route": route_result,
                    "backup_route": None,
                    "found_solution": "no_toll"
                }
            else:
                print(f"⚠️ Route 'sans péage' contient {toll_count} péage(s) - sera utilisée comme backup")
                cost = sum(t.get("cost", 0) for t in tolls_on_route)
                duration = toll_free_route["features"][0]["properties"]["summary"]["duration"]
                backup_result = ResultFormatter.format_route_result(
                    toll_free_route, cost, duration, toll_count
                )
                return {
                    "primary_route": backup_result,
                    "backup_route": None,
                    "found_solution": "plus_one"  # Si on demandait 0 et qu'on a > 0, c'est un dépassement
                }
                
        except Exception as e:
            return TollErrorHandler.handle_ors_error(e, "route_sans_peage")
    
    def _find_route_with_exact_tolls(self, coordinates, target_tolls, veh_class):
        """
        Trouve une route avec exactement target_tolls péages.
        
        Stratégie :
        1. Si target_tolls = 0, utiliser évitement complet des péages
        2. Sinon, tester différentes stratégies d'évitement intelligent
        """
        print(f"🔍 Recherche route avec exactement {target_tolls} péages...")
        
        if target_tolls == 0:
            # Cas spécial : route sans péage
            return self._try_avoiding_route_for_exact(coordinates, 0, veh_class)
        
        # Pour les autres cas, utiliser l'évitement intelligent mais viser l'exactitude
        return self._find_route_targeting_exact_count(coordinates, target_tolls, veh_class)
    
    def _find_route_targeting_exact_count(self, coordinates, target_tolls, veh_class):
        """
        Trouve une route visant exactement target_tolls péages.
        """
        try:
            # 1. Essayer route directe d'abord
            base_route_result = self._try_base_route_for_exact(coordinates, target_tolls, veh_class)
            if base_route_result:
                return base_route_result
            
            # 2. Utiliser l'évitement intelligent pour viser le nombre exact
            smart_route_result = self._try_smart_toll_avoidance_for_exact(coordinates, target_tolls, veh_class)
            if smart_route_result:
                return smart_route_result
            
            # 3. En dernier recours, essayer route avec évitement total (pour target_tolls = 0 seulement)
            if target_tolls == 0:
                avoiding_route_result = self._try_avoiding_route_for_exact(coordinates, target_tolls, veh_class)
                if avoiding_route_result:
                    return avoiding_route_result
            
            return None
            
        except Exception as e:
            print(f"❌ Erreur recherche route exacte {target_tolls} péages: {e}")
            return None
    
    def _try_base_route_for_exact(self, coordinates, target_tolls, veh_class):
        """Teste si la route directe a exactement target_tolls péages."""
        try:
            base_route = self.route_calculator.get_base_route_with_tracking(coordinates)
            
            # Analyser les péages
            tolls_dict = self.route_calculator.locate_and_cost_tolls(
                base_route, veh_class, f"locate_tolls_base_exact_{target_tolls}"
            )
            tolls_on_route = tolls_dict["on_route"]
            toll_count = len(tolls_on_route)
            
            print(f"Route directe: {toll_count} péages (cible: {target_tolls})")
            
            # Vérifier si elle a exactement le nombre voulu
            if toll_count == target_tolls:
                cost = sum(t.get("cost", 0) for t in tolls_on_route)
                duration = base_route["features"][0]["properties"]["summary"]["duration"]
                
                return ResultFormatter.format_route_result(
                    base_route, cost, duration, toll_count
                )
            
            return None
            
        except Exception as e:
            print(f"❌ Erreur route directe exacte: {e}")
            return None
    
    def _try_avoiding_route_for_exact(self, coordinates, target_tolls, veh_class):
        """Teste la route avec évitement pour exactement target_tolls péages."""
        try:
            avoiding_route = self.route_calculator.get_route_avoid_tollways_with_tracking(coordinates)
            
            # Analyser les péages
            tolls_dict = self.route_calculator.locate_and_cost_tolls(
                avoiding_route, veh_class, f"locate_tolls_avoiding_exact_{target_tolls}"
            )
            tolls_on_route = tolls_dict["on_route"]
            toll_count = len(tolls_on_route)
            
            print(f"Route évitement: {toll_count} péages (cible: {target_tolls})")
            
            # Vérifier si elle a exactement le nombre voulu
            if toll_count == target_tolls:
                cost = sum(t.get("cost", 0) for t in tolls_on_route)
                duration = avoiding_route["features"][0]["properties"]["summary"]["duration"]
                
                return ResultFormatter.format_route_result(
                    avoiding_route, cost, duration, toll_count
                )
            
            return None
            
        except Exception as e:
            print(f"❌ Erreur route évitement exacte: {e}")
            return None
    
    def _try_smart_toll_avoidance_for_exact(self, coordinates, target_tolls, veh_class):
        """
        Évitement intelligent pour viser exactement target_tolls péages.
        """
        try:
            # Calculer route de base pour analyser les péages
            base_route = self.route_calculator.get_base_route_with_tracking(coordinates)
            tolls_dict = self.route_calculator.locate_and_cost_tolls(
                base_route, veh_class, f"locate_tolls_smart_exact_{target_tolls}"
            )
            tolls_on_route = tolls_dict["on_route"]
            total_tolls = len(tolls_on_route)
            
            print(f"Route de base: {total_tolls} péages, cible exacte: {target_tolls}")
            
            # Si route de base a exactement le bon nombre, la retourner
            if total_tolls == target_tolls:
                cost = sum(t.get("cost", 0) for t in tolls_on_route)
                duration = base_route["features"][0]["properties"]["summary"]["duration"]
                return ResultFormatter.format_route_result(
                    base_route, cost, duration, total_tolls
                )
            
            # Si on a trop de péages, essayer d'en éviter quelques-uns
            if total_tolls > target_tolls:
                tolls_to_avoid = total_tolls - target_tolls
                print(f"Besoin d'éviter exactement {tolls_to_avoid} péages")
                
                # Tester l'évitement intelligent avec différentes stratégies
                result = self._test_exact_avoidance_strategies(tolls_on_route, tolls_to_avoid, coordinates, target_tolls, veh_class)
                if result:
                    return result
            
            # Si on a pas assez de péages, on ne peut pas en ajouter facilement
            # Retourner None pour laisser les autres priorités s'exprimer
            return None
            
        except Exception as e:
            print(f"❌ Erreur évitement intelligent exact: {e}")
            return None
    
    def _test_exact_avoidance_strategies(self, tolls_on_route, tolls_to_avoid, coordinates, target_tolls, veh_class):
        """Teste différentes stratégies pour éviter exactement tolls_to_avoid péages."""
        
        # Stratégie 1: Éviter les péages les plus coûteux
        result = self._test_exact_avoidance_by_cost(tolls_on_route, tolls_to_avoid, coordinates, target_tolls, veh_class)
        if result:
            return result
        
        # Stratégie 2: Éviter par position géographique
        result = self._test_exact_avoidance_by_position(tolls_on_route, tolls_to_avoid, coordinates, target_tolls, veh_class)
        if result:
            return result
        
        # Stratégie 3: Évitement avec différents rayons
        result = self._test_exact_avoidance_variable_radius(tolls_on_route, tolls_to_avoid, coordinates, target_tolls, veh_class)
        if result:
            return result
        
        return None
    
    def _test_exact_avoidance_by_cost(self, tolls_on_route, tolls_to_avoid, coordinates, target_tolls, veh_class):
        """Teste l'évitement des péages les plus coûteux pour atteindre exactement target_tolls."""
        sorted_tolls = sorted(tolls_on_route, key=lambda t: t.get("cost", 0), reverse=True)
        
        tolls_to_avoid_list = sorted_tolls[:tolls_to_avoid]
        
        for radius in [400, 700, 1000]:
            result = self._test_toll_avoidance_exact(tolls_to_avoid_list, coordinates, target_tolls, veh_class, radius)
            if result and result['toll_count'] == target_tolls:
                print(f"✅ Évitement par coût réussi (rayon {radius}m)")
                return result
        
        return None
    
    def _test_exact_avoidance_by_position(self, tolls_on_route, tolls_to_avoid, coordinates, target_tolls, veh_class):
        """Teste l'évitement par position géographique."""
        if len(tolls_on_route) < 3:
            return None
        
        # Diviser en groupes et tester
        third = len(tolls_on_route) // 3
        groups = [
            tolls_on_route[:third],           # Début
            tolls_on_route[-third:],          # Fin  
            tolls_on_route[third:-third] if third > 0 else []  # Milieu
        ]
        
        for i, group in enumerate(groups):
            if len(group) >= tolls_to_avoid:
                tolls_to_avoid_list = group[:tolls_to_avoid]
                
                for radius in [600, 900]:
                    result = self._test_toll_avoidance_exact(tolls_to_avoid_list, coordinates, target_tolls, veh_class, radius)
                    if result and result['toll_count'] == target_tolls:
                        print(f"✅ Évitement par position réussi (groupe {['début', 'fin', 'milieu'][i]}, rayon {radius}m)")
                        return result
        
        return None
    
    def _test_exact_avoidance_variable_radius(self, tolls_on_route, tolls_to_avoid, coordinates, target_tolls, veh_class):
        """Teste avec différents rayons et combinaisons."""
        sorted_tolls = sorted(tolls_on_route, key=lambda t: t.get("cost", 0), reverse=True)
        
        # Tester avec différents nombres de péages à éviter autour de la cible
        for avoid_variation in range(max(1, tolls_to_avoid - 1), min(len(sorted_tolls), tolls_to_avoid + 2) + 1):
            tolls_to_avoid_list = sorted_tolls[:avoid_variation]
            
            for radius in [250, 500, 800, 1200]:
                result = self._test_toll_avoidance_exact(tolls_to_avoid_list, coordinates, target_tolls, veh_class, radius)
                if result and result['toll_count'] == target_tolls:
                    print(f"✅ Évitement variable réussi ({avoid_variation} péages évités, rayon {radius}m)")
                    return result
        
        return None
    
    def _test_toll_avoidance_exact(self, tolls_to_avoid_list, coordinates, target_tolls, veh_class, radius_m):
        """Teste l'évitement d'une liste de péages pour atteindre exactement target_tolls."""
        try:
            # Préparer les données pour poly_utils
            tolls_for_avoidance = []
            for toll in tolls_to_avoid_list:
                tolls_for_avoidance.append({
                    "longitude": toll.get("lon", toll.get("longitude")),
                    "latitude": toll.get("lat", toll.get("latitude"))
                })
            
            if not tolls_for_avoidance:
                return None
            
            # Créer le multipolygon d'évitement
            from src.utils.poly_utils import avoidance_multipolygon
            avoid_poly = avoidance_multipolygon(tolls_for_avoidance, radius_m=radius_m)
            
            # Calculer route alternative
            alternative_route = self.route_calculator.get_route_avoiding_polygons_with_tracking(
                coordinates, avoid_poly
            )
            
            if alternative_route:
                # Analyser les péages de la route alternative
                alt_tolls_dict = self.route_calculator.locate_and_cost_tolls(
                    alternative_route, veh_class, f"locate_tolls_exact_test_{target_tolls}"
                )
                alt_tolls_on_route = alt_tolls_dict["on_route"]
                alt_toll_count = len(alt_tolls_on_route)
                
                # Retourner le résultat même s'il n'est pas exact (pour comparaison)
                if alt_toll_count <= target_tolls + 2:  # Accepter une marge
                    cost = sum(t.get("cost", 0) for t in alt_tolls_on_route)
                    duration = alternative_route["features"][0]["properties"]["summary"]["duration"]
                    
                    return ResultFormatter.format_route_result(
                        alternative_route, cost, duration, alt_toll_count
                    )
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ Erreur test évitement exact: {e}")
            return None
        """
        Trouve une route avec au maximum max_tolls_limit péages.
        
        Nouvelle logique intelligente :
        1. Route directe (si elle respecte la limite)
        2. Évitement intelligent des péages les plus coûteux 
        3. Route avec évitement total (en dernier recours)
        """
        print(f"🔍 Recherche route avec ≤ {max_tolls_limit} péages...")
        
        # 1. Essayer route directe d'abord
        base_route_result = self._try_base_route(coordinates, max_tolls_limit, veh_class)
        if base_route_result:
            print(f"✅ Route directe trouvée avec {base_route_result['toll_count']} péages (≤ {max_tolls_limit})")
            return base_route_result
        
        # 2. Si route directe a trop de péages, essayer évitement intelligent
        if max_tolls_limit > 0:
            smart_route_result = self._try_smart_toll_avoidance(coordinates, max_tolls_limit, veh_class)
            if smart_route_result:
                print(f"✅ Route évitement intelligent trouvée avec {smart_route_result['toll_count']} péages (≤ {max_tolls_limit})")
                return smart_route_result
        
        # 3. En dernier recours, essayer route avec évitement total
        avoiding_route_result = self._try_avoiding_route(coordinates, max_tolls_limit, veh_class)
        if avoiding_route_result:
            print(f"✅ Route évitement total trouvée avec {avoiding_route_result['toll_count']} péages (≤ {max_tolls_limit})")
            return avoiding_route_result
        
        print(f"❌ Aucune route trouvée avec ≤ {max_tolls_limit} péages")
        return None
    
    def _try_base_route(self, coordinates, max_tolls_limit, veh_class):
        """Essaie la route directe."""
        try:
            base_route = self.route_calculator.get_base_route_with_tracking(coordinates)
            
            # Analyser les péages
            tolls_dict = self.route_calculator.locate_and_cost_tolls(
                base_route, veh_class, "locate_tolls_base_route"
            )
            tolls_on_route = tolls_dict["on_route"]
            toll_count = len(tolls_on_route)
            
            print(f"Route directe: {toll_count} péages trouvés")
            
            # Vérifier si elle respecte la limite
            if toll_count <= max_tolls_limit:
                cost = sum(t.get("cost", 0) for t in tolls_on_route)
                duration = base_route["features"][0]["properties"]["summary"]["duration"]
                
                return ResultFormatter.format_route_result(
                    base_route, cost, duration, toll_count
                )
            
            return None
            
        except Exception as e:
            print(f"❌ Erreur route directe: {e}")
            return None
    
    def _try_avoiding_route(self, coordinates, max_tolls_limit, veh_class):
        """Essaie la route avec évitement des péages."""
        try:
            avoiding_route = self.route_calculator.get_route_avoid_tollways_with_tracking(coordinates)
            
            # Analyser les péages
            tolls_dict = self.route_calculator.locate_and_cost_tolls(
                avoiding_route, veh_class, "locate_tolls_avoiding"
            )
            tolls_on_route = tolls_dict["on_route"]
            toll_count = len(tolls_on_route)
            
            print(f"Route évitement: {toll_count} péages trouvés")
            
            # Vérifier si elle respecte la limite
            if toll_count <= max_tolls_limit:
                cost = sum(t.get("cost", 0) for t in tolls_on_route)
                duration = avoiding_route["features"][0]["properties"]["summary"]["duration"]
                
                return ResultFormatter.format_route_result(
                    avoiding_route, cost, duration, toll_count
                )
            
            return None
            
        except Exception as e:
            print(f"❌ Erreur route évitement: {e}")
            return None
    
    def _try_smart_toll_avoidance(self, coordinates, max_tolls_limit, veh_class):
        """
        Essaie un évitement intelligent des péages pour respecter la contrainte.
        
        Nouvelle logique améliorée :
        1. Calculer route de base pour identifier tous les péages
        2. Tester différentes stratégies d'évitement :
           - Évitement des péages les plus éloignés du trajet principal
           - Évitement par groupes géographiques 
           - Évitement des péages les plus coûteux
        """
        try:
            # Calculer route de base pour analyser les péages
            base_route = self.route_calculator.get_base_route_with_tracking(coordinates)
            tolls_dict = self.route_calculator.locate_and_cost_tolls(
                base_route, veh_class, "locate_tolls_smart_avoidance"
            )
            tolls_on_route = tolls_dict["on_route"]
            total_tolls = len(tolls_on_route)
            
            print(f"Route de base: {total_tolls} péages, limite: {max_tolls_limit}")
            
            # Si route de base respecte déjà la limite, la retourner
            if total_tolls <= max_tolls_limit:
                cost = sum(t.get("cost", 0) for t in tolls_on_route)
                duration = base_route["features"][0]["properties"]["summary"]["duration"]
                return ResultFormatter.format_route_result(
                    base_route, cost, duration, total_tolls
                )
            
            # Calculer combien de péages éviter
            tolls_to_avoid = total_tolls - max_tolls_limit
            print(f"Besoin d'éviter {tolls_to_avoid} péages sur {total_tolls}")
            
            # Stratégie 1: Éviter les péages les plus coûteux
            result = self._try_avoid_most_expensive(tolls_on_route, tolls_to_avoid, coordinates, max_tolls_limit, veh_class)
            if result:
                return result
            
            # Stratégie 2: Éviter par groupes géographiques (début/fin de trajet)
            result = self._try_avoid_geographical_groups(tolls_on_route, tolls_to_avoid, coordinates, max_tolls_limit, veh_class)
            if result:
                return result
            
            # Stratégie 3: Évitement progressif avec différents rayons
            result = self._try_progressive_avoidance(tolls_on_route, tolls_to_avoid, coordinates, max_tolls_limit, veh_class)
            if result:
                return result
            
            print("❌ Toutes les stratégies d'évitement intelligent ont échoué")
            return None
            
        except Exception as e:
            print(f"❌ Erreur évitement intelligent: {e}")
            return None
    
    def _try_avoid_most_expensive(self, tolls_on_route, tolls_to_avoid, coordinates, max_tolls_limit, veh_class):
        """Tente d'éviter les péages les plus coûteux."""
        print("🔄 Stratégie 1: Évitement des péages les plus coûteux")
        
        # Trier par coût décroissant
        sorted_tolls = sorted(tolls_on_route, key=lambda t: t.get("cost", 0), reverse=True)
        
        for avoid_count in range(tolls_to_avoid, min(tolls_to_avoid + 3, len(sorted_tolls)) + 1):
            tolls_to_avoid_list = sorted_tolls[:avoid_count]
            result = self._test_toll_avoidance(tolls_to_avoid_list, coordinates, max_tolls_limit, veh_class, 500)  # 500m rayon
            if result:
                print(f"✅ Succès avec évitement des {avoid_count} péages les plus coûteux")
                return result
        
        return None
    
    def _try_avoid_geographical_groups(self, tolls_on_route, tolls_to_avoid, coordinates, max_tolls_limit, veh_class):
        """Tente d'éviter les péages par groupes géographiques."""
        print("🔄 Stratégie 2: Évitement par groupes géographiques")
        
        if len(tolls_on_route) < 4:  # Pas assez de péages pour faire des groupes
            return None
        
        # Diviser les péages en groupes (début, milieu, fin)
        third = len(tolls_on_route) // 3
        
        groups = [
            tolls_on_route[:third],           # Début
            tolls_on_route[-third:],          # Fin  
            tolls_on_route[third:-third] if third > 0 else []  # Milieu
        ]
        
        # Tester l'évitement de chaque groupe
        for i, group in enumerate(groups):
            if len(group) >= tolls_to_avoid:
                group_to_avoid = group[:tolls_to_avoid]
                result = self._test_toll_avoidance(group_to_avoid, coordinates, max_tolls_limit, veh_class, 800)  # 800m rayon
                if result:
                    print(f"✅ Succès avec évitement du groupe {['début', 'fin', 'milieu'][i]}")
                    return result
        
        return None
    
    def _try_progressive_avoidance(self, tolls_on_route, tolls_to_avoid, coordinates, max_tolls_limit, veh_class):
        """Tente un évitement progressif avec différents rayons."""
        print("🔄 Stratégie 3: Évitement progressif")
        
        # Trier par coût pour avoir une base de départ
        sorted_tolls = sorted(tolls_on_route, key=lambda t: t.get("cost", 0), reverse=True)
        
        # Tester avec différents rayons et nombres de péages à éviter
        radii = [300, 600, 1000, 1500]  # Rayons en mètres
        
        for radius in radii:
            for avoid_count in range(tolls_to_avoid, min(tolls_to_avoid + 4, len(sorted_tolls)) + 1):
                tolls_to_avoid_list = sorted_tolls[:avoid_count]
                result = self._test_toll_avoidance(tolls_to_avoid_list, coordinates, max_tolls_limit, veh_class, radius)
                if result:
                    print(f"✅ Succès avec évitement de {avoid_count} péages (rayon {radius}m)")
                    return result
        
        return None
    
    def _test_toll_avoidance(self, tolls_to_avoid_list, coordinates, max_tolls_limit, veh_class, radius_m):
        """Teste l'évitement d'une liste de péages avec un rayon donné."""
        try:
            print(f"   Test évitement de {len(tolls_to_avoid_list)} péages (rayon {radius_m}m)")
            
            # Préparer les données pour poly_utils
            tolls_for_avoidance = []
            for toll in tolls_to_avoid_list:
                tolls_for_avoidance.append({
                    "longitude": toll.get("lon", toll.get("longitude")),
                    "latitude": toll.get("lat", toll.get("latitude"))
                })
            
            if not tolls_for_avoidance:
                return None
            
            # Créer le multipolygon d'évitement avec le rayon spécifié
            from src.utils.poly_utils import avoidance_multipolygon
            avoid_poly = avoidance_multipolygon(tolls_for_avoidance, radius_m=radius_m)
            
            # Calculer route alternative
            alternative_route = self.route_calculator.get_route_avoiding_polygons_with_tracking(
                coordinates, avoid_poly
            )
            
            if alternative_route:
                # Analyser les péages de la route alternative
                alt_tolls_dict = self.route_calculator.locate_and_cost_tolls(
                    alternative_route, veh_class, f"locate_tolls_avoid_test"
                )
                alt_tolls_on_route = alt_tolls_dict["on_route"]
                alt_toll_count = len(alt_tolls_on_route)
                
                print(f"   Route alternative: {alt_toll_count} péages")
                
                # Vérifier si cette route respecte la contrainte
                if alt_toll_count <= max_tolls_limit:
                    cost = sum(t.get("cost", 0) for t in alt_tolls_on_route)
                    duration = alternative_route["features"][0]["properties"]["summary"]["duration"]
                    
                    return ResultFormatter.format_route_result(
                        alternative_route, cost, duration, alt_toll_count
                    )
            return None
            
        except Exception as e:
            print(f"   ⚠️ Erreur test évitement: {e}")
            return None
