"""
enhanced_constraint_strategy.py
-----------------------------

Stratégie améliorée qui combine l'approche classique avec la segmentation.
Essaie d'abord l'approche classique, puis la segmentation si échec.
"""

from src.services.toll.simple_constraint_strategy import SimpleConstraintStrategy
from src.services.toll.segmentation.segmentation_strategy import SegmentationStrategy
from src.services.toll.segmentation.progressive_avoidance_strategy import ProgressiveAvoidanceStrategy
from src.services.toll.constants import TollOptimizationConfig as Config
from benchmark.performance_tracker import performance_tracker


class EnhancedConstraintStrategy:
    """
    Stratégie améliorée combinant approche classique + segmentation + évitement progressif.
    Essaie d'abord l'approche classique rapide, puis la segmentation, puis l'évitement progressif si échec.
    """
    
    def __init__(self, ors_service):
        """
        Initialise la stratégie améliorée.
        
        Args:
            ors_service: Service ORS pour les appels API
        """
        self.ors = ors_service
        self.classic_strategy = SimpleConstraintStrategy(ors_service)
        self.segmentation_strategy = SegmentationStrategy(ors_service)
        self.progressive_strategy = ProgressiveAvoidanceStrategy(ors_service)

    def find_route_respecting_constraint(self, coordinates, max_tolls, veh_class=Config.DEFAULT_VEH_CLASS, use_segmentation=True, use_progressive=True, start_with_progressive=False, start_with_segmentation=False):
        """
        Trouve une route respectant la contrainte avec stratégie hybride.
        
        Args:
            coordinates: Liste de coordonnées [départ, arrivée]
            max_tolls: Nombre maximum de péages autorisés
            veh_class: Classe de véhicule
            use_segmentation: Si True, utilise la segmentation 
            use_progressive: Si True, utilise l'évitement progressif
            start_with_progressive: Si True, commence par l'évitement progressif
            start_with_segmentation: Si True, commence par la segmentation
               
        Returns:
            dict: Route trouvée avec métadonnées de solution
        """
        with performance_tracker.measure_operation("enhanced_constraint_strategy", {
            "max_tolls": max_tolls,
            "use_segmentation": use_segmentation,
            "use_progressive": use_progressive,
            "start_with_progressive": start_with_progressive,
            "start_with_segmentation": start_with_segmentation
        }):
            print(f"🚀 === STRATÉGIE AMÉLIORÉE : ≤ {max_tolls} péages ===")
            
            # Si segmentation en priorité
            if start_with_segmentation and use_segmentation:
                print("🧩 Tentative segmentation (priorité)...")
                segmentation_result = self._try_segmentation_approach(coordinates, max_tolls, veh_class)
                
                if segmentation_result and segmentation_result.get("found_solution") != "none":
                    print(f"✅ Segmentation réussie : {segmentation_result.get('found_solution')}")
                    return segmentation_result
                    
                print("🧩 Segmentation échouée, essai des autres stratégies...")
            
            # Si évitement progressif en priorité
            elif start_with_progressive and use_progressive:
                print("🎯 Tentative évitement progressif (priorité)...")
                progressive_result = self._try_progressive_approach(coordinates, max_tolls, veh_class)
                
                if progressive_result and progressive_result.get("found_solution") != "none":
                    print(f"✅ Évitement progressif réussi : {progressive_result.get('found_solution')}")
                    return progressive_result
                    
                print("🎯 Évitement progressif échoué, essai des autres stratégies...")
            
            # Si segmentation forcée uniquement (ancien comportement)
            if use_segmentation and not use_progressive and not start_with_progressive and not start_with_segmentation:
                print("🧩 Utilisation directe de la segmentation")
                return self._try_segmentation_approach(coordinates, max_tolls, veh_class)
            
            # 1. Essayer l'approche classique (rapide)
            print("⚡ Tentative approche classique...")
            classic_result = self.classic_strategy.find_route_respecting_constraint(
                coordinates, max_tolls, veh_class
            )
            
            # Vérifier si l'approche classique a trouvé une solution acceptable
            if classic_result and classic_result.get("found_solution") != "none":
                print(f"✅ Approche classique réussie : {classic_result.get('found_solution')}")
                return classic_result
            
            # 2. Si approche classique a échoué, essayer la segmentation
            if use_segmentation:
                print("🧩 Approche classique échouée, tentative segmentation...")
                segmentation_result = self._try_segmentation_approach(coordinates, max_tolls, veh_class)
                
                if segmentation_result and segmentation_result.get("found_solution") != "none":
                    print(f"✅ Segmentation réussie : {segmentation_result.get('found_solution')}")
                    return segmentation_result
            
            # 3. Si tout a échoué, essayer l'évitement progressif (si pas déjà fait)
            if use_progressive and not start_with_progressive:
                print("🎯 Segmentation échouée, tentative évitement progressif...")
                return self._try_progressive_approach(coordinates, max_tolls, veh_class)
            
            # Si toutes les stratégies ont échoué
            print("❌ Toutes les stratégies ont échoué")
            return self._format_segmentation_failure(max_tolls)
    
    def _try_segmentation_approach(self, coordinates, max_tolls, veh_class):
        """
        Essaie l'approche de segmentation.
        
        Args:
            coordinates: Coordonnées [départ, arrivée]
            max_tolls: Nombre maximum de péages
            veh_class: Classe de véhicule
            
        Returns:
            dict: Résultat de la segmentation au format compatible
        """
        try:
            print("🧩 === DÉBUT SEGMENTATION ===")
            # 1. Obtenir la route de base simple (sans évitement) pour identifier les péages
            print("📡 Calcul route de base pour identification des péages...")
            # Utiliser le route_calculator existant pour la cohérence
            base_route_data = self.classic_strategy.route_tester.route_calculator.get_base_route_with_tracking(coordinates)
            print("Clés de base_route_data :", list(base_route_data.keys()))
            
            if not base_route_data or 'features' not in base_route_data or not base_route_data['features']:
                print(f"❌ Impossible d'obtenir la route de base")
                return self._format_segmentation_failure(max_tolls)            # 2. Localiser les péages sur la route de base
            from src.services.toll_locator import locate_tolls
            tolls_dict = locate_tolls(base_route_data)
            
            # Extraire les péages sur la route et à proximité
            tolls_on_route = tolls_dict.get("on_route", [])
            tolls_nearby = tolls_dict.get("nearby", [])
            available_tolls = tolls_on_route + tolls_nearby
            
            print(f"📍 {len(tolls_on_route)} péages sur la route, {len(tolls_nearby)} à proximité = {len(available_tolls)} péages disponibles")
            
            # 3. Utiliser la stratégie de segmentation
            segmentation_result = self.segmentation_strategy.find_route_with_segmentation(
                coordinates, available_tolls, max_tolls, veh_class
            )            
            # 3. Formater le résultat au format compatible
            if segmentation_result:
                print("✅ Segmentation réussie")
                return self._format_segmentation_success(segmentation_result, max_tolls)
            else:
                print("❌ Segmentation échouée")
                return self._format_segmentation_failure(max_tolls)
                
        except Exception as e:
            print(f"❌ Erreur segmentation : {e}")
            return self._format_segmentation_failure(max_tolls)
    
    def _try_progressive_approach(self, coordinates, max_tolls, veh_class):
        """
        Essaie l'approche d'évitement progressif.
        
        Args:
            coordinates: Coordonnées [départ, arrivée]
            max_tolls: Nombre maximum de péages
            veh_class: Classe de véhicule
            
        Returns:
            dict: Résultat de l'évitement progressif au format compatible
        """
        try:
            print("🎯 === DÉBUT ÉVITEMENT PROGRESSIF ===")
            
            # Utiliser la stratégie d'évitement progressif
            progressive_result = self.progressive_strategy.find_route_with_progressive_avoidance(
                coordinates, max_tolls, veh_class
            )
            
            # Formater le résultat au format compatible
            if progressive_result:
                print("✅ Évitement progressif réussi")
                return self._format_progressive_success(progressive_result, max_tolls)
            else:
                print("❌ Évitement progressif échoué")
                return self._format_segmentation_failure(max_tolls)
                
        except Exception as e:
            print(f"❌ Erreur évitement progressif : {e}")
            return self._format_segmentation_failure(max_tolls)

    def _format_segmentation_success(self, segmentation_result, max_tolls):
        """
        Formate un succès de segmentation au format compatible.
        
        Args:
            segmentation_result: Résultat de la segmentation
            max_tolls: Nombre maximum de péages demandé
            
        Returns:
            dict: Résultat formaté
        """
        actual_tolls = segmentation_result.get('toll_count', 0)
        
        # Déterminer le type de solution
        if actual_tolls <= max_tolls:
            solution_type = "within_limit_segmentation"
        else:
            solution_type = "backup_segmentation"
        
        return {
            "primary_route": segmentation_result,
            "backup_route": None,
            "found_solution": solution_type,
            "requested_max": max_tolls,
            "actual_tolls": actual_tolls,
            "strategy_used": "segmentation"
        }
    
    def _format_progressive_success(self, progressive_result, max_tolls):
        """
        Formate un succès d'évitement progressif au format compatible.
        
        Args:
            progressive_result: Résultat de l'évitement progressif
            max_tolls: Nombre maximum de péages demandé
            
        Returns:
            dict: Résultat formaté
        """
        actual_tolls = progressive_result.get('toll_count', 0)
        
        # Déterminer le type de solution
        if actual_tolls <= max_tolls:
            solution_type = "within_limit_progressive"
        else:
            solution_type = "backup_progressive"
        
        return {
            "primary_route": progressive_result,
            "backup_route": None,
            "found_solution": solution_type,
            "requested_max": max_tolls,
            "actual_tolls": actual_tolls,
            "strategy_used": "progressive_avoidance"
        }
    
    def _format_segmentation_failure(self, max_tolls):
        """
        Formate un échec de segmentation au format compatible.
        
        Args:
            max_tolls: Nombre maximum de péages demandé
            
        Returns:
            dict: Résultat d'échec formaté
        """
        return {
            "primary_route": None,
            "backup_route": None,
            "found_solution": "none",
            "requested_max": max_tolls,
            "actual_tolls": None,
            "strategy_used": "segmentation_failed"
        }
