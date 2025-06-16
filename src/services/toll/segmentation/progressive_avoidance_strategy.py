"""
progressive_avoidance_strategy.py
---------------------------------

Responsabilité : Stratégie d'évitement progressif des péages.
Au lieu de générer des combinaisons artificielles, teste l'évitement de chaque péage
de la route de base pour trouver des alternatives réelles et optimales.
"""

from src.services.toll_locator import locate_tolls
from src.services.toll.route_calculator import RouteCalculator
from src.services.toll.constants import TollOptimizationConfig as Config
from src.services.common.result_formatter import ResultFormatter


class ProgressiveAvoidanceStrategy:
    """
    Stratégie d'évitement progressif.
    Responsabilité unique : trouver des routes alternatives en évitant progressivement
    les péages de la route de base.
    """
    
    def __init__(self, ors_service):
        """
        Initialise la stratégie d'évitement progressif.
        Args:
            ors_service: Service ORS pour les appels API
        """
        self.ors = ors_service
        self.route_calculator = RouteCalculator(ors_service)
    
    def find_route_with_progressive_avoidance(self, coordinates, max_tolls, veh_class=Config.DEFAULT_VEH_CLASS):
        """
        Trouve une route alternative en évitant progressivement les péages de la route de base.
        
        Args:
            coordinates: Coordonnées [départ, arrivée]
            max_tolls: Nombre maximum de péages autorisés
            veh_class: Classe de véhicule
            
        Returns:
            dict: Route optimisée ou None si échec
        """
        print(f"🔄 === ÉVITEMENT PROGRESSIF : ≤ {max_tolls} péages ===")
        
        # Cas spécial : si max_tolls = 0, calculer directement une route sans péage
        if max_tolls == 0:
            print("🚫 max_tolls = 0 : Calcul direct d'une route sans péage...")
            return self._calculate_no_toll_route(coordinates, veh_class)
        
        # 1. Calculer la route de base et identifier les péages
        try:
            print(f"📍 1. Analyse de la route de base...")
            base_route = self.route_calculator.get_base_route_with_tracking(coordinates)
            tolls_dict = self.route_calculator.locate_and_cost_tolls(base_route, veh_class)
            base_tolls = tolls_dict.get("on_route", [])
            base_toll_count = len(base_tolls)
            
            print(f"   Route de base: {base_toll_count} péages détectés")
            
            # Si la route de base respecte déjà la limite
            if base_toll_count <= max_tolls:
                print(f"✅ Route de base OK: {base_toll_count} ≤ {max_tolls} péages")
                base_cost = sum(t.get("cost", 0) for t in base_tolls)
                base_duration = base_route["features"][0]["properties"]["summary"]["duration"]
                return ResultFormatter.format_route_result(base_route, base_cost, base_duration, base_toll_count)
            
            # Calculer combien de péages éviter
            tolls_to_remove = base_toll_count - max_tolls
            print(f"🎯 Besoin d'éviter {tolls_to_remove} péages pour atteindre {max_tolls}")
            
        except Exception as e:
            print(f"❌ Erreur analyse route de base: {e}")
            return None
          # 2. Tester l'évitement progressif
        return self._test_progressive_avoidance(coordinates, base_tolls, tolls_to_remove, max_tolls, veh_class)
    
    def _test_progressive_avoidance(self, coordinates, base_tolls, tolls_to_remove, max_tolls, veh_class):
        """
        Teste l'évitement progressif des péages.
        
        Args:
            coordinates: Coordonnées [départ, arrivée]
            base_tolls: Péages de la route de base
            tolls_to_remove: Nombre de péages à éviter
            max_tolls: Nombre maximum de péages autorisés (objectif)
            veh_class: Classe de véhicule
            
        Returns:
            dict: Meilleure route trouvée ou None
        """
        from itertools import combinations
        
        print(f"🧪 2. Test d'évitement progressif...")
        
        best_result = None
        best_toll_count = float('inf')
        best_cost = float('inf')
        # Tester toutes les combinaisons possibles de péages à éviter
        for r in range(1, min(tolls_to_remove + 1, len(base_tolls)) + 1):
            print(f"\n🔍 Test évitement de {r} péages...")
            
            for tolls_to_avoid in combinations(base_tolls, r):
                toll_ids = [t.get('id', 'NO_ID') for t in tolls_to_avoid]
                print(f"   🚫 Évitement: {', '.join(toll_ids)}")
                
                # Tester cette combinaison d'évitement
                result = self._test_avoidance_combination(coordinates, tolls_to_avoid, veh_class)
                
                if result:
                    route_tolls = result.get('toll_count', 0)
                    route_cost = result.get('cost', 0)
                    
                    print(f"   ✅ Trouvé: {route_tolls} péages, {route_cost:.2f}€")
                    
                    # Garder le meilleur résultat (moins de péages, puis moins cher)
                    if (route_tolls < best_toll_count or 
                        (route_tolls == best_toll_count and route_cost < best_cost)):
                        best_result = result
                        best_toll_count = route_tolls
                        best_cost = route_cost
                        print(f"   🏆 Nouveau meilleur résultat!")
                        
                        # Si on a atteint l'objectif exact, on peut s'arrêter
                        if route_tolls <= max_tolls:
                            print(f"🎯 OBJECTIF ATTEINT: {route_tolls} ≤ {max_tolls} péages")
                            break
                else:
                    print(f"   ❌ Échec évitement")
            
            # Si on a atteint l'objectif, sortir de la boucle externe aussi
            if best_toll_count <= max_tolls:
                print(f"✅ Objectif respecté: {best_toll_count} ≤ {max_tolls} péages")
                break        
        if best_result:
            print(f"🎉 SUCCÈS évitement progressif: {best_toll_count} péages, {best_cost:.2f}€")
            return best_result
        else:
            print(f"❌ ÉCHEC: Aucune amélioration trouvée")
            return None

    def _test_avoidance_combination(self, coordinates, tolls_to_avoid, veh_class):
        """
        Teste une combinaison spécifique d'évitement avec rayons progressifs.
        
        Args:
            coordinates: Coordonnées [départ, arrivée]
            tolls_to_avoid: Péages à éviter
            veh_class: Classe de véhicule
            
        Returns:
            dict: Route résultante ou None si échec
        """
        try:
            from src.utils.poly_utils import avoidance_multipolygon
            # Rayons progressifs pour trouver des alternatives plus éloignées
            # Incluant des rayons plus grands pour les détours longs
            radius_sequence = [500, 1000, 1500, 2000]
            
            for attempt, radius in enumerate(radius_sequence, 1):
                try:
                    print(f"   🔄 Tentative évitement {attempt}/{len(radius_sequence)} (rayon {radius}m)")
                    
                    # Créer les polygones d'évitement avec le rayon actuel
                    avoid_polygons = avoidance_multipolygon(tolls_to_avoid, radius_m=radius)
                    
                    # Calculer la route avec évitement
                    alternative_route = self.ors.get_route_avoiding_polygons(
                        coordinates, avoid_polygons, include_tollways=True
                    )
                    
                    if not alternative_route or 'features' not in alternative_route:
                        print(f"   ❌ Tentative {attempt}: Aucune route trouvée")
                        continue
                    
                    # Analyser la route alternative
                    tolls_dict = self.route_calculator.locate_and_cost_tolls(alternative_route, veh_class)
                    route_tolls = tolls_dict.get("on_route", [])
                    route_cost = sum(t.get("cost", 0) for t in route_tolls)
                    route_duration = alternative_route["features"][0]["properties"]["summary"]["duration"]
                    
                    print(f"   ✅ Tentative {attempt}: {len(route_tolls)} péages, {route_cost:.2f}€")
                    
                    # Formater et retourner le premier résultat valide
                    return ResultFormatter.format_route_result(
                        alternative_route, route_cost, route_duration, len(route_tolls)
                    )
                    
                except Exception as e:
                    print(f"   ⚠️ Tentative {attempt} échouée: {e}")
                    continue
            
            # Aucune tentative n'a réussi
            print(f"   ❌ Toutes les tentatives d'évitement ont échoué")
            return None
            
        except Exception as e:
            print(f"⚠️ Erreur test évitement: {e}")
            return None

    def _calculate_no_toll_route(self, coordinates, veh_class):
        """
        Calcule directement une route sans péage.
        Utilise la même méthode que les autres stratégies.
        
        Args:
            coordinates: Coordonnées [départ, arrivée]
            veh_class: Classe de véhicule
            
        Returns:
            dict: Route sans péage formatée ou None si échec
        """
        try:
            print("🚫 Calcul d'une route évitant tous les péages...")
            
            # Utiliser la même méthode que SimpleConstraintStrategy
            toll_free_route = self.route_calculator.get_route_avoid_tollways_with_tracking(coordinates)
            
            if not toll_free_route or 'features' not in toll_free_route:
                print("❌ Impossible de calculer une route sans péage")
                return None
            
            # Analyser la route pour confirmation
            tolls_dict = self.route_calculator.locate_and_cost_tolls(toll_free_route, veh_class)
            route_tolls = tolls_dict.get("on_route", [])
            route_cost = sum(t.get("cost", 0) for t in route_tolls)
            route_duration = toll_free_route["features"][0]["properties"]["summary"]["duration"]
            toll_count = len(route_tolls)
            
            print(f"✅ Route sans péage calculée: {toll_count} péages, {route_cost:.2f}€")
            
            # Formater le résultat
            return ResultFormatter.format_route_result(
                toll_free_route, route_cost, route_duration, toll_count
            )
            
        except Exception as e:
            print(f"❌ Erreur calcul route sans péage: {e}")
            return None
