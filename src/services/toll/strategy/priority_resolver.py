"""
priority_resolver.py
-------------------

Gestionnaire des priorités pour la recherche de routes respectant les contraintes de péages.
Implémente la logique de priorité : exact, +1, -1, sans péage.
"""


class PriorityResolver:
    """
    Résolveur de priorités pour la recherche de routes avec contraintes de péages.
    
    Logique de priorité :
    1. Route avec exactement max_tolls péages (priorité 1)
    2. Route avec max_tolls + 1 péages (priorité 2) 
    3. Route avec max_tolls - 1 péages (priorité 3)
    4. Route sans péage (priorité 4)
    """
    def __init__(self, exact_toll_finder, route_tester=None):
        self.exact_toll_finder = exact_toll_finder
        self.route_tester = route_tester  # Ajout pour accéder au route_calculator
    
    def find_route_with_priority_system(self, coordinates, max_tolls, veh_class):
        """
        Trouve une route en respectant le système de priorité.
        
        Args:
            coordinates: Coordonnées de départ et arrivée
            max_tolls: Nombre maximum de péages autorisés
            veh_class: Classe de véhicule
            
        Returns:
            dict: {
                "primary_route": meilleure_route_trouvée,
                "backup_route": route_alternative ou None,
                "found_solution": "exact" | "plus_one" | "minus_one" | "no_toll" | "none"
            }
        """
        print(f"=== Recherche route optimale pour {max_tolls} péages (priorité exacte) ===")
        
        # Cas spécial : aucun péage autorisé
        if max_tolls == 0:
            return self._handle_no_toll_case(coordinates, veh_class)
        
        # Recherche séquentielle : s'arrêter dès qu'une solution est trouvée
        
        # 1. Priorité 1: Exactement max_tolls péages
        print(f"🎯 Recherche priorité 1: exactement {max_tolls} péages...")
        exact_route = self.exact_toll_finder.find_route_with_exact_tolls(coordinates, max_tolls, veh_class)
        if exact_route:
            print(f"✅ Solution EXACTE trouvée: {exact_route['toll_count']} péages (= {max_tolls})")
            return {
                "primary_route": exact_route,
                "backup_route": None,
                "found_solution": "exact"
            }
        
        # 2. Priorité 2: max_tolls + 1 péages
        print(f"🔄 Recherche priorité 2: {max_tolls + 1} péages...")
        plus_one_route = self.exact_toll_finder.find_route_with_exact_tolls(coordinates, max_tolls + 1, veh_class)
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
            minus_one_route = self.exact_toll_finder.find_route_with_exact_tolls(coordinates, max_tolls - 1, veh_class)
            if minus_one_route:
                print(f"✅ Solution -1 trouvée: {minus_one_route['toll_count']} péages (= {max_tolls - 1})")
                return {
                    "primary_route": minus_one_route,
                    "backup_route": None,
                    "found_solution": "minus_one"
                }
        
        # 4. Priorité 4: Route sans péage (dernier recours)
        print(f"🚫 Recherche priorité 4: route sans péage...")
        no_toll_route = self.exact_toll_finder.find_route_with_exact_tolls(coordinates, 0, veh_class)
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
        from src.services.common.toll_messages import TollMessages
        from src.services.common.result_formatter import ResultFormatter
        from src.services.toll.error_handler import TollErrorHandler
        
        print(TollMessages.SEARCH_NO_TOLL)
        
        try:
            # Utiliser le route_tester pour obtenir la route d'évitement
            toll_free_route_result = self.route_tester.test_avoiding_route(coordinates, 0, veh_class, exact_match=False)
            
            if toll_free_route_result and toll_free_route_result['toll_count'] == 0:
                print("✅ Route sans péage trouvée")
                return {
                    "primary_route": toll_free_route_result,
                    "backup_route": None,
                    "found_solution": "no_toll"
                }
            elif toll_free_route_result:
                print(f"⚠️ Route 'sans péage' contient {toll_free_route_result['toll_count']} péage(s) - sera utilisée comme backup")
                return {
                    "primary_route": toll_free_route_result,
                    "backup_route": None,
                    "found_solution": "plus_one"  # Si on demandait 0 et qu'on a > 0, c'est un dépassement
                }
            else:
                # Essayer la route de base comme dernier recours
                base_route_result = self.route_tester.test_base_route(coordinates, 0, veh_class, exact_match=False)
                if base_route_result:
                    return {
                        "primary_route": base_route_result,
                        "backup_route": None,
                        "found_solution": "plus_one" if base_route_result['toll_count'] > 0 else "no_toll"
                    }
                
                # Aucune solution trouvée
                return {
                    "primary_route": None,
                    "backup_route": None,
                    "found_solution": "none"
                }
                
        except Exception as e:
            return TollErrorHandler.handle_ors_error(e, "route_sans_peage")
