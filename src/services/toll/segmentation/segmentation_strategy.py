"""
segmentation_strategy.py
-----------------------

Coordinateur principal de la stratégie de segmentation.
Orchestre : génération de combinaisons → calcul segments → assemblage route.
"""

from src.services.toll.segmentation.combination_generator import CombinationGenerator
from src.services.toll.segmentation.segment_calculator import SegmentCalculator
from src.services.toll.segmentation.route_assembler import RouteAssembler
from src.services.toll.constants import TollOptimizationConfig as Config
from benchmark.performance_tracker import performance_tracker


class SegmentationStrategy:
    """
    Stratégie de segmentation pour optimisation des routes avec péages.
    Coordinateur principal qui orchestre tout le processus.
    """
    
    def __init__(self, ors_service):
        """
        Initialise la stratégie de segmentation.
        
        Args:
            ors_service: Service ORS pour les appels API        """
        self.ors = ors_service
        self.combination_generator = CombinationGenerator()
        self.segment_calculator = SegmentCalculator(ors_service)
        self.route_assembler = RouteAssembler()
    
    def find_route_with_segmentation(self, coordinates, available_tolls, max_tolls, veh_class=Config.DEFAULT_VEH_CLASS):
        """
        Trouve une route en utilisant la stratégie de segmentation.
        
        LOGIQUE COMPLÈTE (comme dans simple_constraint_strategy) :
        1. Vérifier route de base (si ≤ max_tolls → retourner directement)
        2. Si max_tolls = 0 → route sans péages  
        3. Sinon → générer combinaisons avec EXACTEMENT max_tolls péages
        4. Calculer segments séquentiels péage1→péage2→péage3→...
        
        Args:
            coordinates: [départ, arrivée] 
            available_tolls: Péages disponibles sur/proche de la route de base
            max_tolls: Nombre EXACT de péages autorisés
            veh_class: Classe de véhicule
            
        Returns:
            dict: Route trouvée ou None si échec
        """
        with performance_tracker.measure_operation("segmentation_strategy", {
            "max_tolls": max_tolls,
            "available_tolls_count": len(available_tolls)
        }):
            print(f"🧩 === STRATÉGIE SEGMENTATION : exactement {max_tolls} péages ===")
            
            # 1. VÉRIFICATION ROUTE DE BASE
            print(f"🔍 1. Vérification route de base...")
            try:
                from src.services.toll.route_calculator import RouteCalculator
                route_calculator = RouteCalculator(self.ors)
                
                base_route = route_calculator.get_base_route_with_tracking(coordinates)
                tolls_dict = route_calculator.locate_and_cost_tolls(base_route, veh_class)
                tolls_on_base_route = tolls_dict.get("on_route", [])
                base_toll_count = len(tolls_on_base_route)
                
                print(f"   Route de base: {base_toll_count} péages")
                
                if base_toll_count <= max_tolls:
                    print(f"✅ Route de base OK: {base_toll_count} ≤ {max_tolls} péages")
                    # Formater et retourner la route de base
                    from src.services.common.result_formatter import ResultFormatter
                    base_cost = sum(t.get("cost", 0) for t in tolls_on_base_route)
                    base_duration = base_route["features"][0]["properties"]["summary"]["duration"]
                    return ResultFormatter.format_route_result(base_route, base_cost, base_duration, base_toll_count)
                else:
                    print(f"🔧 Route de base a {base_toll_count} > {max_tolls} péages, segmentation nécessaire")
                    
            except Exception as e:
                print(f"⚠️ Erreur vérification route de base: {e}")
            
            # 2. CAS SPÉCIAL: max_tolls = 0 (route sans péages)
            if max_tolls == 0:
                print(f"🚫 2. Recherche route sans péages...")
                try:
                    # Utiliser la logique d'évitement complet comme dans simple_constraint_strategy
                    from src.services.toll.strategy.intelligent_avoidance import IntelligentAvoidance
                    from src.services.toll.strategy.route_tester import RouteTester
                    route_tester = RouteTester(self.ors)
                    intelligent_avoidance = IntelligentAvoidance(route_tester)
                    
                    no_toll_result, status = intelligent_avoidance.find_route_completely_toll_free(coordinates, veh_class)
                    if no_toll_result and status == "NO_TOLL_SUCCESS":
                        print(f"✅ Route sans péages trouvée")
                        return no_toll_result
                    else:
                        print(f"❌ Impossible de trouver une route sans péages")
                        return None
                        
                except Exception as e:
                    print(f"⚠️ Erreur route sans péages: {e}")
                    return None
            
            # 3. GÉNÉRATION DE COMBINAISONS AVEC EXACTEMENT max_tolls PÉAGES
            print(f"🧮 3. Génération combinaisons avec exactement {max_tolls} péages...")
            
            departure, arrival = coordinates[0], coordinates[1]
            # Générer les combinaisons VALIDES avec exactement max_tolls
            combinations = self.combination_generator.generate_valid_combinations(
                departure, arrival, available_tolls, max_tolls, veh_class
            )
            
            print(f"📋 {len(combinations)} combinaisons générées pour {len(available_tolls)} péages disponibles")
            
            if not combinations:
                print("❌ Aucune combinaison générée")
                return None              
            # 2. Tester les combinaisons une par une (ordre de coût croissant)
            for i, combination in enumerate(combinations):
                # Extraire les IDs des péages de la combinaison
                toll_ids = [toll.get('id', f'TOLL_{j}') for j, toll in enumerate(combination['tolls'])]
                toll_ids_str = ', '.join(toll_ids)
                print(f"\n🎯 Test combinaison {i+1}/{len(combinations)} (coût estimé: {combination['estimated_cost']:.2f}€)")
                print(f"   📍 Péages: {toll_ids_str}")
                
                route_result = self._test_combination(combination, available_tolls, veh_class)
                
                if route_result:
                    print(f"✅ SUCCÈS avec la combinaison {i+1} !")
                    
                    # Recalculer le coût correct en utilisant la détection de péages sur la route finale
                    try:
                        from src.services.toll.route_calculator import RouteCalculator
                        route_calculator = RouteCalculator(self.ors)
                        
                        # Extraire la route GeoJSON du résultat
                        final_route = route_result.get('route')
                        if final_route:
                            # Localiser et coûter les péages sur la route finale
                            tolls_dict = route_calculator.locate_and_cost_tolls(final_route, veh_class)
                            detected_tolls = tolls_dict.get("on_route", [])
                            correct_cost = sum(t.get("cost", 0) for t in detected_tolls)
                            correct_toll_count = len(detected_tolls)
                            
                            # Mettre à jour le résultat avec le coût correct
                            route_result['cost'] = round(correct_cost, 2)
                            route_result['toll_count'] = correct_toll_count
                            
                            print(f"💰 Coût final recalculé: {correct_cost:.2f}€ pour {correct_toll_count} péages")
                        
                    except Exception as e:
                        print(f"⚠️ Erreur recalcul coût: {e}")
                    
                    return route_result
                
                print(f"❌ Échec combinaison {i+1}")
            
            # 3. Aucune combinaison n'a fonctionné
            print("❌ ÉCHEC : Toutes les combinaisons ont échoué")
            return None
    
    def _test_combination(self, combination, available_tolls, veh_class):
        """
        Teste une combinaison spécifique en calculant tous ses segments.
        
        Args:
            combination: Combinaison à tester
                        Format: {'waypoints': [départ, péage1, ..., arrivée], 'estimated_cost': float}
            available_tolls: Tous les péages disponibles (pour déterminer lesquels éviter)
            veh_class: Classe de véhicule
        Returns:
            dict: Route assemblée ou None si échec
        """
        waypoints = combination['waypoints']
        segments_results = []
        
        print(f"  📍 Waypoints: {len(waypoints)} points")
        # DEBUG: Afficher les détails des waypoints
        for i, wp in enumerate(waypoints):
            if isinstance(wp, dict) and 'id' in wp:
                wp_id = wp.get('id', 'NO_ID')
                # Debug détaillé pour voir toutes les clés
                print(f"    Waypoint {i}: {wp_id}")
                print(f"      Clés disponibles: {list(wp.keys())}")
                wp_coords = [wp.get('lon', wp.get('longitude', 'NO_LON')), wp.get('lat', wp.get('latitude', 'NO_LAT'))]
                print(f"      Coordonnées: {wp_coords}")
            else:
                print(f"    Waypoint {i}: {wp}")
        
        # Déterminer quels péages éviter (tous sauf ceux dans les waypoints)
        tolls_to_avoid = self._get_tolls_to_avoid(combination['tolls'], available_tolls)
        # Calculer chaque segment : waypoint[i] → waypoint[i+1]
        for i in range(len(waypoints) - 1):
            from_point = waypoints[i]
            to_point = waypoints[i + 1]
            
            print(f"    🔧 Segment {i+1}/{len(waypoints)-1}")            
            # Calculer le segment avec évitement intelligent des péages non autorisés
            # On autorise les péages de la combinaison, on évite les autres
            segment_result = self.segment_calculator.calculate_segment_with_smart_avoidance(
                from_point, to_point, combination['tolls'], veh_class
            )
            
            # Vérifier le succès du segment
            if not segment_result.get('success', False):
                error_msg = segment_result.get('error', 'Erreur inconnue')
                print(f"    ❌ Échec segment {i+1}: {error_msg}")
                return None  # Abandon de cette combinaison
            
            print(f"    ✅ Segment {i+1} réussi")
            segments_results.append(segment_result)
        
        # Tous les segments ont réussi, assembler la route
        print(f"  🔨 Assemblage de {len(segments_results)} segments...")
        assembled_route = self.route_assembler.assemble_route(segments_results, waypoints)
        if assembled_route:
            print(f"  ✅ Route assemblée avec succès")
            return assembled_route
        else:
            print(f"  ❌ Échec assemblage")
            return None

    def _get_tolls_to_avoid(self, selected_tolls, available_tolls):
        """
        Détermine quels péages éviter en excluant ceux sélectionnés dans la combinaison.
        
        Args:
            selected_tolls: Péages sélectionnés dans la combinaison (à garder)
            available_tolls: Tous les péages disponibles
            
        Returns:
            list: Péages à éviter (available_tolls - selected_tolls)
        """
        if not selected_tolls:
            return available_tolls
        
        # Extraire les IDs des péages sélectionnés
        selected_ids = set()
        for toll in selected_tolls:
            if isinstance(toll, dict):
                selected_ids.add(toll.get('id'))
            else:
                selected_ids.add(str(toll))
        
        # DEBUG: Afficher les péages sélectionnés
        print(f"    🎯 Péages sélectionnés (à garder): {', '.join(selected_ids)}")
        
        # Filtrer les péages à éviter
        tolls_to_avoid = []
        for toll in available_tolls:
            toll_id = toll.get('id') if isinstance(toll, dict) else str(toll)
            if toll_id not in selected_ids:
                tolls_to_avoid.append(toll)
        
        # DEBUG: Afficher les péages à éviter
        avoid_ids = [t.get('id', 'NO_ID') for t in tolls_to_avoid]
        print(f"    🚫 {len(tolls_to_avoid)} péages à éviter: {', '.join(avoid_ids[:5])}{'...' if len(avoid_ids) > 5 else ''}")
        
        return tolls_to_avoid
