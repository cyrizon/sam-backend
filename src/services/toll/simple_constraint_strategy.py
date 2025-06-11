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
        Trouve une route respectant la contrainte de péages avec backup.
        
        Logique :
        1. Chercher route avec ≤ max_tolls péages
        2. Si pas trouvé, chercher route avec max_tolls + 1 péages (backup)
        3. Retourner la meilleure option trouvée
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            max_tolls: Nombre maximum de péages autorisés
            veh_class: Classe de véhicule pour le calcul des coûts
            
        Returns:
            dict: {
                "primary_route": route_respectant_contrainte ou None,
                "backup_route": route_max_tolls_plus_1 ou None,
                "found_solution": "primary" | "backup" | "none"
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
            print(f"=== Recherche route contrainte {max_tolls} péages (+ backup {max_tolls + 1}) ===")
            
            # Cas spécial : aucun péage autorisé
            if max_tolls == 0:
                return self._handle_no_toll_case(coordinates, veh_class)
            
            # 1. Chercher route respectant la contrainte exacte
            primary_route = self._find_route_within_limit(coordinates, max_tolls, veh_class)
            
            # 2. Chercher route backup (max_tolls + 1)
            backup_route = self._find_route_within_limit(coordinates, max_tolls + 1, veh_class)
            
            # 3. Déterminer la meilleure solution
            return self._select_best_solution(primary_route, backup_route, max_tolls)
    
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
                    "found_solution": "primary"
                }
            else:
                print(f"⚠️ Route 'sans péage' contient {toll_count} péage(s) - sera utilisée comme backup")
                cost = sum(t.get("cost", 0) for t in tolls_on_route)
                duration = toll_free_route["features"][0]["properties"]["summary"]["duration"]
                backup_result = ResultFormatter.format_route_result(
                    toll_free_route, cost, duration, toll_count
                )
                return {
                    "primary_route": None,
                    "backup_route": backup_result,
                    "found_solution": "backup"
                }
                
        except Exception as e:
            return TollErrorHandler.handle_ors_error(e, "route_sans_peage")
    
    def _find_route_within_limit(self, coordinates, max_tolls_limit, veh_class):
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
    
    def _select_best_solution(self, primary_route, backup_route, max_tolls):
        """
        Sélectionne la meilleure solution selon la priorité.
        
        Priorité :
        1. primary_route (≤ max_tolls)
        2. backup_route (max_tolls + 1)
        3. aucune solution
        """
        if primary_route:
            print(f"🎯 Solution PRIMAIRE trouvée : {primary_route['toll_count']} péages (≤ {max_tolls})")
            return {
                "primary_route": primary_route,
                "backup_route": backup_route,
                "found_solution": "primary"
            }
        elif backup_route:
            print(f"🔄 Solution BACKUP trouvée : {backup_route['toll_count']} péages (= {max_tolls + 1})")
            return {
                "primary_route": None,
                "backup_route": backup_route,
                "found_solution": "backup"
            }
        else:
            print("❌ Aucune solution trouvée (ni primaire ni backup)")
            return {
                "primary_route": None,
                "backup_route": None,
                "found_solution": "none"
            }
