"""
intelligent_avoidance.py
-----------------------

Stratégies d'évitement intelligent de péages.
Contient les différents algorithmes pour éviter sélectivement des péages
selon différents critères (coût, position géographique, etc.).
"""

from src.services.toll.route_calculator import RouteCalculator
from src.services.common.result_formatter import ResultFormatter
from src.services.toll_locator import get_all_open_tolls_by_proximity
from src.utils.route_utils import is_toll_open_system


class IntelligentAvoidance:
    """
    Gestionnaire des stratégies d'évitement intelligent de péages.
    Intègre les meilleures pratiques des anciennes stratégies spécialisées.
    """
    
    def __init__(self, route_tester):
        self.route_tester = route_tester
        self.route_calculator = route_tester.route_calculator
    
    # === MÉTHODES ORIGINALES ===
    
    def find_route_with_intelligent_avoidance(self, coordinates, tolls_on_route, target_tolls, veh_class, exact_match=False):
        """
        Trouve une route en utilisant l'évitement intelligent.
        
        Args:
            coordinates: Coordonnées de départ et arrivée
            tolls_on_route: Liste des péages sur la route de base
            target_tolls: Nombre de péages cible
            veh_class: Classe de véhicule
            exact_match: Si True, cherche exactement target_tolls, sinon ≤ target_tolls
            
        Returns:
            dict: Route trouvée ou None
        """
        total_tolls = len(tolls_on_route)
        
        if exact_match:
            return self._find_exact_toll_count(coordinates, tolls_on_route, target_tolls, veh_class)
        else:
            return self._find_within_limit(coordinates, tolls_on_route, target_tolls, veh_class)
    
    def _find_exact_toll_count(self, coordinates, tolls_on_route, target_tolls, veh_class):
        """Trouve une route avec exactement target_tolls péages."""
        total_tolls = len(tolls_on_route)
        
        if total_tolls == target_tolls:
            # Déjà le bon nombre, retourner la route de base
            return self._format_base_route(coordinates, tolls_on_route, veh_class)
        elif total_tolls > target_tolls:
            # Trop de péages, en éviter quelques-uns
            tolls_to_avoid = total_tolls - target_tolls
            return self._test_exact_avoidance_strategies(tolls_on_route, tolls_to_avoid, coordinates, target_tolls, veh_class)
        else:
            # Pas assez de péages, difficile d'en ajouter
            return None
    
    def _find_within_limit(self, coordinates, tolls_on_route, max_tolls_limit, veh_class):
        """Trouve une route avec ≤ max_tolls_limit péages."""
        total_tolls = len(tolls_on_route)
        
        if total_tolls <= max_tolls_limit:
            # Déjà dans la limite, retourner la route de base
            return self._format_base_route(coordinates, tolls_on_route, veh_class)
        
        # Calculer combien de péages éviter
        tolls_to_avoid = total_tolls - max_tolls_limit
        print(f"Besoin d'éviter {tolls_to_avoid} péages sur {total_tolls}")
        
        # Tester les différentes stratégies
        strategies = [
            ("Évitement des péages les plus coûteux", self._try_avoid_most_expensive),
            ("Évitement par groupes géographiques", self._try_avoid_geographical_groups),
            ("Évitement progressif", self._try_progressive_avoidance)
        ]
        
        for strategy_name, strategy_func in strategies:
            print(f"🔄 {strategy_name}")
            result = strategy_func(tolls_on_route, tolls_to_avoid, coordinates, max_tolls_limit, veh_class)
            if result:
                return result
        
        return None
    
    def _test_exact_avoidance_strategies(self, tolls_on_route, tolls_to_avoid, coordinates, target_tolls, veh_class):
        """Teste différentes stratégies pour éviter exactement tolls_to_avoid péages."""
        
        strategies = [
            ("Évitement par coût", self._test_exact_avoidance_by_cost),
            ("Évitement par position", self._test_exact_avoidance_by_position),
            ("Évitement variable rayon", self._test_exact_avoidance_variable_radius)
        ]
        
        for strategy_name, strategy_func in strategies:
            result = strategy_func(tolls_on_route, tolls_to_avoid, coordinates, target_tolls, veh_class)
            if result:
                print(f"✅ {strategy_name} réussi")
                return result
        
        return None
    
    def _test_exact_avoidance_by_cost(self, tolls_on_route, tolls_to_avoid, coordinates, target_tolls, veh_class):
        """Évite les péages les plus coûteux pour atteindre exactement target_tolls."""
        sorted_tolls = sorted(tolls_on_route, key=lambda t: t.get("cost", 0), reverse=True)
        tolls_to_avoid_list = sorted_tolls[:tolls_to_avoid]
        
        for radius in [400, 700, 1000]:
            result = self.route_tester.test_toll_avoidance_with_polygon(
                tolls_to_avoid_list, coordinates, target_tolls, veh_class, radius, exact_match=True
            )
            if result and result['toll_count'] == target_tolls:
                return result
        
        return None
    
    def _test_exact_avoidance_by_position(self, tolls_on_route, tolls_to_avoid, coordinates, target_tolls, veh_class):
        """Évite par position géographique."""
        if len(tolls_on_route) < 3:
            return None
        
        # Diviser en groupes
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
                    result = self.route_tester.test_toll_avoidance_with_polygon(
                        tolls_to_avoid_list, coordinates, target_tolls, veh_class, radius, exact_match=True
                    )
                    if result and result['toll_count'] == target_tolls:
                        return result
        
        return None
    
    def _test_exact_avoidance_variable_radius(self, tolls_on_route, tolls_to_avoid, coordinates, target_tolls, veh_class):
        """Teste avec différents rayons et combinaisons."""
        sorted_tolls = sorted(tolls_on_route, key=lambda t: t.get("cost", 0), reverse=True)
        
        # Tester avec différents nombres de péages à éviter autour de la cible
        for avoid_variation in range(max(1, tolls_to_avoid - 1), min(len(sorted_tolls), tolls_to_avoid + 2) + 1):
            tolls_to_avoid_list = sorted_tolls[:avoid_variation]
            
            for radius in [250, 500, 800, 1200]:
                result = self.route_tester.test_toll_avoidance_with_polygon(
                    tolls_to_avoid_list, coordinates, target_tolls, veh_class, radius, exact_match=True
                )
                if result and result['toll_count'] == target_tolls:
                    return result
        
        return None
    
    def _try_avoid_most_expensive(self, tolls_on_route, tolls_to_avoid, coordinates, max_tolls_limit, veh_class):
        """Évite les péages les plus coûteux."""
        sorted_tolls = sorted(tolls_on_route, key=lambda t: t.get("cost", 0), reverse=True)
        
        for avoid_count in range(tolls_to_avoid, min(tolls_to_avoid + 3, len(sorted_tolls)) + 1):
            tolls_to_avoid_list = sorted_tolls[:avoid_count]
            result = self.route_tester.test_toll_avoidance_with_polygon(
                tolls_to_avoid_list, coordinates, max_tolls_limit, veh_class, 500
            )
            if result:
                print(f"✅ Succès avec évitement des {avoid_count} péages les plus coûteux")
                return result
        
        return None
    
    def _try_avoid_geographical_groups(self, tolls_on_route, tolls_to_avoid, coordinates, max_tolls_limit, veh_class):
        """Évite par groupes géographiques."""
        if len(tolls_on_route) < 4:
            return None
        
        # Diviser en groupes
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
                result = self.route_tester.test_toll_avoidance_with_polygon(
                    group_to_avoid, coordinates, max_tolls_limit, veh_class, 800
                )
                if result:
                    print(f"✅ Succès avec évitement du groupe {['début', 'fin', 'milieu'][i]}")
                    return result
        
        return None
    
    def _try_progressive_avoidance(self, tolls_on_route, tolls_to_avoid, coordinates, max_tolls_limit, veh_class):
        """Évitement progressif avec différents rayons."""
        sorted_tolls = sorted(tolls_on_route, key=lambda t: t.get("cost", 0), reverse=True)
        radii = [300, 600, 1000, 1500]
        
        for radius in radii:
            for avoid_count in range(tolls_to_avoid, min(tolls_to_avoid + 4, len(sorted_tolls)) + 1):
                tolls_to_avoid_list = sorted_tolls[:avoid_count]
                result = self.route_tester.test_toll_avoidance_with_polygon(
                    tolls_to_avoid_list, coordinates, max_tolls_limit, veh_class, radius
                )
                if result:
                    print(f"✅ Succès avec évitement de {avoid_count} péages (rayon {radius}m)")
                    return result
        
        return None
    
    def _format_base_route(self, coordinates, tolls_on_route, veh_class):
        """Formate la route de base avec les informations de péages."""
        from src.services.common.result_formatter import ResultFormatter
        
        try:
            # Récupérer la route de base via le route_tester
            base_route, _, _ = self.route_tester.get_base_route_tolls(coordinates, veh_class)
            
            if base_route is not None:
                cost = sum(t.get("cost", 0) for t in tolls_on_route)
                duration = base_route["features"][0]["properties"]["summary"]["duration"]
                toll_count = len(tolls_on_route)
                
                return ResultFormatter.format_route_result(
                    base_route, cost, duration, toll_count
                )
            
            return None
        except Exception as e:
            print(f"❌ Erreur formatage route de base: {e}")
            return None
    
    # === NOUVELLES MÉTHODES INTÉGRÉES ===
    
    def find_route_completely_toll_free(self, coordinates, veh_class):
        """
        Trouve une route complètement sans péage en utilisant avoid_features.
        Intégré depuis NoTollStrategy.
        
        Args:
            coordinates: Coordonnées [départ, arrivée]
            veh_class: Classe de véhicule
            
        Returns:
            tuple: (route_data, status_code) ou (None, error_status)
        """
        try:
            # Utiliser l'évitement complet des péages d'ORS
            toll_free_route = self.route_calculator.get_route_avoid_tollways_with_tracking(coordinates)
            
            # Vérifier s'il reste encore des péages malgré l'évitement
            tolls_dict = self.route_calculator.locate_and_cost_tolls(toll_free_route, veh_class)
            tolls_on_route = tolls_dict["on_route"]
            
            if not tolls_on_route:
                # Vraiment sans péage
                duration = toll_free_route["features"][0]["properties"]["summary"]["duration"]
                return ResultFormatter.format_route_result(toll_free_route, 0, duration, 0), "NO_TOLL_SUCCESS"
            else:
                # Il reste quelques péages malgré l'évitement
                cost = sum(t.get("cost", 0) for t in tolls_on_route)
                duration = toll_free_route["features"][0]["properties"]["summary"]["duration"]
                return ResultFormatter.format_route_result(
                    toll_free_route, cost, duration, len(tolls_on_route)
                ), "SOME_TOLLS_PRESENT"
                
        except Exception as e:
            return None, f"ERROR_NO_TOLL_ROUTE: {e}"
    
    def find_route_with_one_open_toll(self, coordinates, veh_class):
        """
        Trouve une route passant par exactement un péage à système ouvert.
        Intégré depuis OneOpenTollStrategy.
        
        Args:
            coordinates: Coordonnées [départ, arrivée]
            veh_class: Classe de véhicule
            
        Returns:
            dict: Meilleure route trouvée ou None
        """
        # 1) Obtenir la route de base pour analyser les péages à proximité
        base_route = self.route_calculator.get_base_route_with_tracking(coordinates)
        
        # 2) Trouver tous les péages ouverts à proximité
        open_tolls_nearby = get_all_open_tolls_by_proximity(
            base_route, max_distance_m=100000  # 100km
        )
        
        if not open_tolls_nearby:
            return None
        
        best_route = None
        best_cost = float('inf')
        
        # 3) Tester chaque péage ouvert
        for toll in open_tolls_nearby:
            try:
                # Calculer route en 2 segments: départ → péage → arrivée
                route_result = self._calculate_route_via_open_toll(
                    coordinates, toll, veh_class
                )
                
                if route_result and route_result["cost"] < best_cost:
                    best_route = route_result
                    best_cost = route_result["cost"]
                    
            except Exception as e:
                continue
        
        return best_route
    
    def _calculate_route_via_open_toll(self, coordinates, target_toll, veh_class):
        """
        Calcule une route passant par un péage spécifique en évitant les autres.
        
        Args:
            coordinates: [départ, arrivée]
            target_toll: Péage cible à traverser
            veh_class: Classe de véhicule
            
        Returns:
            dict: Route formatée ou None
        """
        departure = coordinates[0]
        arrival = coordinates[1]
        toll_coords = [target_toll["longitude"], target_toll["latitude"]]
        
        # Segment 1: Départ → Péage
        segment1_coords = [departure, toll_coords]
        segment1_result = self.route_calculator.calculate_route_avoiding_unwanted_tolls(
            segment1_coords, target_toll["id"], "segment1"
        )
        
        if not segment1_result:
            return None
        
        # Segment 2: Péage → Arrivée  
        segment2_coords = [toll_coords, arrival]
        segment2_result = self.route_calculator.calculate_route_avoiding_unwanted_tolls(
            segment2_coords, target_toll["id"], "segment2"
        )
        
        if not segment2_result:
            return None
        
        # Fusionner les deux segments
        merged_route = self._merge_route_segments(
            segment1_result["route"], segment2_result["route"]
        )
        
        # Calculer les métriques finales
        total_tolls = segment1_result["tolls"] + segment2_result["tolls"]
        total_cost = sum(t.get("cost", 0) for t in total_tolls)
        total_duration = (
            segment1_result["route"]["features"][0]["properties"]["summary"]["duration"] +
            segment2_result["route"]["features"][0]["properties"]["summary"]["duration"]
        )
        
        return ResultFormatter.format_route_result(
            merged_route, total_cost, total_duration, len(total_tolls)
        )
    
    def test_optimized_toll_combinations(self, coordinates, all_tolls, max_tolls, veh_class, max_combinations=50):
        """
        Teste des combinaisons de péages à éviter avec optimisations avancées.
        Intégré depuis ManyTollsStrategy avec les meilleures optimisations.
        
        Args:
            coordinates: Coordonnées [départ, arrivée]
            all_tolls: Liste de tous les péages détectés
            max_tolls: Nombre maximum de péages autorisés
            veh_class: Classe de véhicule
            max_combinations: Limite du nombre de combinaisons à tester
            
        Returns:
            dict: Meilleure route trouvée ou None
        """
        from itertools import combinations
        from src.utils.poly_utils import avoidance_multipolygon
        
        if len(all_tolls) <= max_tolls:
            return None  # Pas besoin d'évitement
        
        # Tri par coût décroissant pour éviter d'abord les plus chers
        all_tolls_sorted = sorted(all_tolls, key=lambda t: t.get("cost", 0), reverse=True)
        
        best_route = None
        best_cost = float('inf')
        tested_combinations = set()
        combination_count = 0
        
        # Tester les combinaisons de péages à éviter
        for k in range(1, min(len(all_tolls_sorted), max_combinations) + 1):
            for to_avoid in combinations(all_tolls_sorted, k):
                combination_count += 1
                
                # Signature unique pour éviter les doublons
                sig = tuple(sorted(t["id"] for t in to_avoid))
                if sig in tested_combinations:
                    continue
                tested_combinations.add(sig)
                
                # Heuristique d'arrêt anticipé: éviter si l'économie potentielle est nulle
                potential_saving = sum(t.get("cost", 0) for t in to_avoid)
                if potential_saving <= 0:
                    continue
                
                try:
                    # Créer le polygone d'évitement
                    avoid_poly = avoidance_multipolygon(list(to_avoid))
                    
                    # Calculer la route alternative
                    alt_route = self.route_calculator.get_route_avoiding_polygons_with_tracking(
                        coordinates, avoid_poly
                    )
                    
                    # Analyser la route alternative
                    alt_tolls_dict = self.route_calculator.locate_and_cost_tolls(alt_route, veh_class)
                    alt_tolls_on_route = alt_tolls_dict["on_route"]
                    
                    # Vérifier les contraintes
                    if len(alt_tolls_on_route) <= max_tolls:
                        cost = sum(t.get("cost", 0) for t in alt_tolls_on_route)
                        duration = alt_route["features"][0]["properties"]["summary"]["duration"]
                        
                        if cost < best_cost:
                            best_route = ResultFormatter.format_route_result(
                                alt_route, cost, duration, len(alt_tolls_on_route)
                            )
                            best_cost = cost
                            
                            # Arrêt anticipé si coût nul trouvé
                            if cost == 0:
                                break
                
                except Exception:
                    continue
            
            # Arrêt anticipé si solution parfaite trouvée
            if best_cost == 0:
                break
        
        return best_route
    
    def filter_open_system_tolls(self, tolls_list):
        """
        Filtre les péages pour ne garder que ceux à système ouvert.
        
        Args:
            tolls_list: Liste des péages à filtrer
            
        Returns:
            list: Péages à système ouvert seulement
        """
        return [toll for toll in tolls_list if is_toll_open_system(toll["id"])]
    
    def _merge_route_segments(self, route1, route2):
        """
        Fusionne deux segments de route en évitant les doublons de coordonnées.
        
        Args:
            route1: Premier segment de route
            route2: Deuxième segment de route
            
        Returns:
            dict: Route fusionnée
        """
        from src.utils.route_utils import merge_routes
        return merge_routes(route1, route2)
