"""
exact_toll_finder.py
-------------------

Classe spécialisée dans la recherche de routes avec un nombre exact de péages.
Gère la logique de recherche précise pour respecter exactement une contrainte.
"""

from src.services.toll_locator import get_all_open_tolls_by_proximity


class ExactTollFinder:
    """
    Trouveur de routes avec un nombre exact de péages.
    Intègre les stratégies spécialisées pour différents cas (0, 1, N péages).
    """
    
    def __init__(self, route_tester, intelligent_avoidance):
        self.route_tester = route_tester
        self.intelligent_avoidance = intelligent_avoidance
    
    def find_route_with_exact_tolls(self, coordinates, target_tolls, veh_class):
        """
        Trouve une route avec exactement target_tolls péages.
        Utilise des stratégies spécialisées selon le nombre cible.
        
        Args:
            coordinates: Coordonnées de départ et arrivée
            target_tolls: Nombre exact de péages souhaité
            veh_class: Classe de véhicule
            
        Returns:
            dict: Route trouvée ou None
        """
        print(f"🔍 Recherche route avec exactement {target_tolls} péages...")
        
        # Stratégies spécialisées selon le nombre cible
        if target_tolls == 0:
            return self._find_zero_toll_route(coordinates, veh_class)
        elif target_tolls == 1:
            return self._find_one_toll_route(coordinates, veh_class)
        else:
            return self._find_n_toll_route(coordinates, target_tolls, veh_class)
    
    def _find_zero_toll_route(self, coordinates, veh_class):
        """
        Trouve une route avec 0 péage en utilisant l'évitement complet.
        Stratégie spécialisée issue de NoTollStrategy.
        """
        print("🚫 Stratégie spécialisée: aucun péage")
        result, status = self.intelligent_avoidance.find_route_completely_toll_free(coordinates, veh_class)
        
        if result and status == "NO_TOLL_SUCCESS":
            return result
        return None
    
    def _find_one_toll_route(self, coordinates, veh_class):
        """
        Trouve une route avec exactement 1 péage.
        Priorité aux péages à système ouvert (stratégie issue de OneOpenTollStrategy).
        """
        print("🎯 Stratégie spécialisée: exactement un péage")
        
        # Essayer d'abord avec un péage ouvert (tarif fixe)
        open_toll_route = self.intelligent_avoidance.find_route_with_one_open_toll(coordinates, veh_class)
        if open_toll_route and open_toll_route.get("toll_count") == 1:
            print("✅ Route trouvée avec péage ouvert")
            return open_toll_route
        
        # Sinon, utiliser la stratégie générale pour 1 péage
        return self._find_n_toll_route(coordinates, 1, veh_class)
    
    def _find_n_toll_route(self, coordinates, target_tolls, veh_class):
        """
        Trouve une route avec exactement N péages (N ≥ 2).
        Utilise les combinaisons optimisées.
        """
        print(f"🔢 Stratégie générale: exactement {target_tolls} péages")
        
        # Test de la route de base
        base_result = self.route_tester.test_base_route(coordinates, target_tolls, veh_class, exact_match=True)
        if base_result:
            print("✅ Route de base correspond exactement")
            return base_result
        
        # Utiliser l'évitement intelligent avec contrainte exacte
        route_with_tolls = self.intelligent_avoidance.find_route_with_intelligent_avoidance(
            coordinates, [], target_tolls, veh_class, exact_match=True
        )
        
        return route_with_tolls
    
    def find_best_open_toll_route(self, coordinates, veh_class):
        """
        Trouve la meilleure route avec un péage ouvert.
        Utilise la proximité géographique et le coût comme critères.
        
        Args:
            coordinates: Coordonnées [départ, arrivée]
            veh_class: Classe de véhicule
            
        Returns:
            dict: Meilleure route avec péage ouvert ou None
        """
        # Obtenir la route de base pour l'analyse
        base_route = self.route_tester.route_calculator.get_base_route_with_tracking(coordinates)
        
        # Trouver péages ouverts à proximité (dans un rayon de 100km)
        open_tolls = get_all_open_tolls_by_proximity(base_route, max_distance_m=100000)
        
        if not open_tolls:
            print("❌ Aucun péage ouvert trouvé à proximité")
            return None
        
        print(f"🔍 {len(open_tolls)} péages ouverts trouvés à proximité")
        
        # Filtrer pour ne garder que les péages vraiment ouverts
        verified_open_tolls = self.intelligent_avoidance.filter_open_system_tolls(open_tolls)
        
        if not verified_open_tolls:
            print("❌ Aucun péage à système ouvert vérifié")
            return None
        
        print(f"✅ {len(verified_open_tolls)} péages à système ouvert vérifiés")
        
        # Tester chaque péage ouvert et garder le meilleur
        best_route = None
        best_cost = float('inf')
        best_distance = None
        
        for i, toll in enumerate(verified_open_tolls[:10]):  # Limiter à 10 pour la performance
            print(f"🧪 Test péage ouvert {i+1}/{min(10, len(verified_open_tolls))}: {toll['id']}")
            
            try:
                route_result = self.intelligent_avoidance._calculate_route_via_open_toll(
                    coordinates, toll, veh_class
                )
                
                if route_result:
                    cost = route_result.get("cost", float('inf'))
                    distance = toll.get("distance_to_route", float('inf'))
                    
                    # Critère de sélection: coût + bonus proximité
                    score = cost + (distance / 1000)  # distance en km
                    
                    if score < best_cost:
                        best_route = route_result
                        best_cost = score
                        best_distance = distance
                        print(f"✅ Nouvelle meilleure solution: {cost}€, {distance/1000:.1f}km")
                        
            except Exception as e:
                print(f"❌ Erreur test péage {toll['id']}: {e}")
                continue
        
        if best_route:
            print(f"🎯 Meilleure route trouvée: {best_route['cost']}€, {best_distance/1000:.1f}km du tracé")
        
        return best_route
