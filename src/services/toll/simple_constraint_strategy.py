"""
simple_constraint_strategy.py
----------------------------

Stratégie simplifiée pour respecter les contraintes de péages - VERSION REFACTORISÉE.
Objectif : 
1. Trouver une route avec ≤ max_tolls péages (priorité 1)
2. Si pas trouvé, essayer max_tolls + 1 péages (priorité 2) 
3. Si toujours rien, fallback (priorité 3)

Cette version utilise des classes spécialisées pour une meilleure séparation des responsabilités.
"""

from benchmark.performance_tracker import performance_tracker
from src.services.toll.constants import TollOptimizationConfig as Config
from src.services.toll.error_handler import TollErrorHandler
from src.services.ors_config_manager import ORSConfigManager

# Import des nouvelles classes spécialisées
from src.services.toll.strategy import (
    RouteTester,
    IntelligentAvoidance,
    ExactTollFinder,
    PriorityResolver
)


class SimpleConstraintStrategy:
    """
    Stratégie simplifiée pour respecter les contraintes de péages.
    Approche pragmatique avec backup max_tolls + 1.
    
    Version refactorisée utilisant des classes spécialisées :
    - RouteTester : Tests et validations de routes
    - IntelligentAvoidance : Stratégies d'évitement intelligent
    - ExactTollFinder : Recherche de routes avec nombre exact de péages
    - PriorityResolver : Gestion des priorités de recherche
    """
    
    def __init__(self, ors_service):
        self.ors = ors_service
          # Initialisation des composants spécialisés
        self.route_tester = RouteTester(ors_service)
        self.intelligent_avoidance = IntelligentAvoidance(self.route_tester)
        self.exact_toll_finder = ExactTollFinder(self.route_tester, self.intelligent_avoidance)
        self.priority_resolver = PriorityResolver(self.exact_toll_finder, self.route_tester)
    
    def find_route_respecting_constraint(self, coordinates, max_tolls, veh_class=Config.DEFAULT_VEH_CLASS):
        """
        Trouve une route respectant la contrainte de péages avec l'ancienne logique efficace.
        
        LOGIQUE ORIGINALE RESTAURÉE :
        1. Route avec ≤ max_tolls péages (priorité 1)
        2. Route avec ≤ max_tolls + 1 péages (priorité 2 - backup) 
        3. Route avec ≤ max_tolls - 1 péages (priorité 3)
        4. Fallback général (priorité 4)
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            max_tolls: Nombre maximum de péages autorisés
            veh_class: Classe de véhicule pour le calcul des coûts
            
        Returns:
            dict: Route trouvée avec métadonnées de solution
        """
        # Validation précoce des coordonnées
        try:
            ORSConfigManager.validate_coordinates(coordinates)
        except ValueError as e:
            return TollErrorHandler.handle_ors_error(e, "validation_coordinates")
        
        with performance_tracker.measure_operation("simple_constraint_strategy", {
            "max_tolls": max_tolls
        }):
            print(f"=== RECHERCHE ROUTE AVEC ≤ {max_tolls} PÉAGES (logique originale) ===")
            
            # 1. PRIORITÉ 1: Route avec ≤ max_tolls péages (objectif principal)
            print(f"🎯 Priorité 1: Recherche route avec ≤ {max_tolls} péages...")
            primary_result = self._find_route_within_limit(coordinates, max_tolls, veh_class)
            if primary_result:
                print(f"✅ SUCCÈS Priorité 1: Route trouvée avec {primary_result.get('toll_count', 'N/A')} péages (≤ {max_tolls})")
                return {
                    "primary_route": primary_result,
                    "backup_route": None,
                    "found_solution": "within_limit",
                    "requested_max": max_tolls,
                    "actual_tolls": primary_result.get('toll_count', 0)
                }
            
            # 2. PRIORITÉ 2: Route avec ≤ max_tolls + 1 péages (backup tolérant)
            if max_tolls < 10:  # Limite raisonnable pour éviter les routes avec trop de péages
                print(f"🔄 Priorité 2: Recherche route avec ≤ {max_tolls + 1} péages (backup +1)...")
                backup_result = self._find_route_within_limit(coordinates, max_tolls + 1, veh_class)
                if backup_result and backup_result.get('toll_count', 0) <= max_tolls + 1:
                    print(f"✅ SUCCÈS Priorité 2: Route backup trouvée avec {backup_result.get('toll_count', 'N/A')} péages (≤ {max_tolls + 1})")
                    return {
                        "primary_route": backup_result,
                        "backup_route": None,
                        "found_solution": "backup_plus_one",
                        "requested_max": max_tolls,
                        "actual_tolls": backup_result.get('toll_count', 0)
                    }
            
            # 3. PRIORITÉ 3: Route avec ≤ max_tolls - 1 péages (si max_tolls > 1)
            if max_tolls > 1:
                print(f"📉 Priorité 3: Recherche route avec ≤ {max_tolls - 1} péages (backup -1)...")
                minus_result = self._find_route_within_limit(coordinates, max_tolls - 1, veh_class)
                if minus_result:
                    print(f"✅ SUCCÈS Priorité 3: Route trouvée avec {minus_result.get('toll_count', 'N/A')} péages (≤ {max_tolls - 1})")
                    return {
                        "primary_route": minus_result,
                        "backup_route": None,
                        "found_solution": "backup_minus_one",
                        "requested_max": max_tolls,
                        "actual_tolls": minus_result.get('toll_count', 0)
                    }
            
            # 4. PRIORITÉ 4: Route sans péage (dernier recours)
            if max_tolls > 0:
                print(f"🚫 Priorité 4: Recherche route sans péage (dernier recours)...")
                no_toll_result = self._find_route_within_limit(coordinates, 0, veh_class)
                if no_toll_result:
                    print(f"✅ SUCCÈS Priorité 4: Route sans péage trouvée")
                    return {
                        "primary_route": no_toll_result,
                        "backup_route": None,
                        "found_solution": "no_toll_fallback",
                        "requested_max": max_tolls,
                        "actual_tolls": 0
                    }
            
            # 5. ÉCHEC TOTAL: Aucune solution trouvée
            print("❌ ÉCHEC: Aucune route trouvée dans toutes les priorités")
            return {
                "primary_route": None,
                "backup_route": None,
                "found_solution": "none",
                "requested_max": max_tolls,
                "actual_tolls": None
            }

    def _find_route_within_limit(self, coordinates, toll_limit, veh_class):
        """
        Trouve une route avec ≤ toll_limit péages (logique originale).
        
        Args:
            coordinates: Coordonnées [départ, arrivée]
            toll_limit: Limite de péages (≤)
            veh_class: Classe de véhicule
            
        Returns:
            dict: Route trouvée ou None
        """
        # 1. Test route de base
        base_result = self.route_tester.test_base_route(coordinates, toll_limit, veh_class, exact_match=False)
        if base_result and base_result.get('toll_count', float('inf')) <= toll_limit:
            print(f"  ✅ Route directe OK: {base_result.get('toll_count')} péages ≤ {toll_limit}")
            return base_result
        
        # 2. Si route de base a trop de péages, essayer évitement intelligent
        if toll_limit > 0:
            try:
                base_route_data = self.route_tester.route_calculator.get_base_route_with_tracking(coordinates)
                tolls_dict = self.route_tester.route_calculator.locate_and_cost_tolls(base_route_data, veh_class)
                tolls_on_route = tolls_dict.get("on_route", [])
                
                if len(tolls_on_route) > toll_limit:
                    print(f"  🔧 Route directe a {len(tolls_on_route)} péages > {toll_limit}, essai évitement...")
                    smart_result = self.intelligent_avoidance.find_route_with_intelligent_avoidance(
                        coordinates, tolls_on_route, toll_limit, veh_class, exact_match=False
                    )
                    if smart_result and smart_result.get('toll_count', float('inf')) <= toll_limit:
                        print(f"  ✅ Évitement intelligent OK: {smart_result.get('toll_count')} péages ≤ {toll_limit}")
                        return smart_result
            except Exception as e:
                print(f"  ⚠️ Erreur évitement intelligent: {e}")
        
        # 3. Si toll_limit = 0, essayer évitement complet
        if toll_limit == 0:
            try:
                no_toll_result, status = self.intelligent_avoidance.find_route_completely_toll_free(coordinates, veh_class)
                if no_toll_result and status == "NO_TOLL_SUCCESS":
                    print(f"  ✅ Évitement complet OK: 0 péages")
                    return no_toll_result
            except Exception as e:
                print(f"  ⚠️ Erreur évitement complet: {e}")
        
        print(f"  ❌ Aucune route trouvée avec ≤ {toll_limit} péages")
        return None
    
    # Méthodes de compatibilité pour les anciens appels (si nécessaire)
    def find_route_within_constraint(self, coordinates, max_tolls_limit, veh_class=Config.DEFAULT_VEH_CLASS):
        """
        Méthode de compatibilité : trouve une route avec ≤ max_tolls_limit péages.
        
        Note: Cette méthode est maintenue pour la compatibilité avec l'ancien code.
        Elle utilise directement l'évitement intelligent sans le système de priorité exact.
        """
        print(f"🔍 Recherche route avec ≤ {max_tolls_limit} péages (mode compatibilité)...")
        
        # Validation précoce des coordonnées
        try:
            ORSConfigManager.validate_coordinates(coordinates)
        except ValueError as e:
            return TollErrorHandler.handle_ors_error(e, "validation_coordinates")
        
        with performance_tracker.measure_operation("simple_constraint_strategy_compat", {
            "max_tolls_limit": max_tolls_limit
        }):
            # 1. Essayer route directe d'abord
            base_route_result = self.route_tester.test_base_route(coordinates, max_tolls_limit, veh_class)
            if base_route_result:
                print(f"✅ Route directe trouvée avec {base_route_result['toll_count']} péages (≤ {max_tolls_limit})")
                return base_route_result
            
            # 2. Si route directe a trop de péages, essayer évitement intelligent
            if max_tolls_limit > 0:
                # Analyser la route de base
                base_route, tolls_on_route, toll_count = self.route_tester.get_base_route_tolls(coordinates, veh_class)
                
                if tolls_on_route is not None:
                    smart_route_result = self.intelligent_avoidance.find_route_with_intelligent_avoidance(
                        coordinates, tolls_on_route, max_tolls_limit, veh_class, exact_match=False
                    )
                    if smart_route_result:
                        print(f"✅ Route évitement intelligent trouvée avec {smart_route_result['toll_count']} péages (≤ {max_tolls_limit})")
                        return smart_route_result
            
            # 3. En dernier recours, essayer route avec évitement total
            avoiding_route_result = self.route_tester.test_avoiding_route(coordinates, max_tolls_limit, veh_class)
            if avoiding_route_result:
                print(f"✅ Route évitement total trouvée avec {avoiding_route_result['toll_count']} péages (≤ {max_tolls_limit})")
                return avoiding_route_result
            
            print(f"❌ Aucune route trouvée avec ≤ {max_tolls_limit} péages")
            return None
