"""
intelligent_segmentation_strategy_v3.py
--------------------------------------

Stratégie hybride : utilisation des segments tollways d'ORS + optimisation de sortie en fallback.

Principe :
1. Utiliser les segments tollways naturels d'ORS pour éviter les péages (cas normal)
2. Optimisation de sortie uniquement quand plusieurs péages sur même segment payant (fallback)

Algorithme :
1. Route de base + extraction des segments tollways
2. Identifier péages SUR la route
3. Sélectionner X péages 
4. **NOUVEAU** : Segmentation hybride basée sur tollways + optimisation ciblée
5. Calcul des routes pour chaque segment
6. Assemblage final
"""

from typing import List, Dict, Optional, Tuple
from .intelligent_segmentation_helpers import SegmentationSpecialCases, RouteUtils
from .toll_matcher import TollMatcher, MatchedToll, convert_osm_tolls_to_matched_format
from .toll_deduplicator import TollDeduplicator
from .polyline_intersection import filter_tolls_on_route_strict
from .exit_optimization import ExitOptimizationManager
from .segment_route_calculator import SegmentRouteCalculator
from .route_assembler import RouteAssembler
from benchmark.performance_tracker import performance_tracker
from src.services.osm_data_cache import osm_data_cache


class IntelligentSegmentationStrategyV3:
    """
    Stratégie hybride tollways + optimisation de sortie.
    """
    
    def __init__(self, ors_service, osm_data_file: str = None):
        """Initialise la stratégie hybride."""
        self.ors = ors_service
        self.osm_parser = osm_data_cache._osm_parser
        self.toll_matcher = TollMatcher()
        self.exit_optimizer = ExitOptimizationManager(self.osm_parser, self.toll_matcher, self.ors)
        self.special_cases = SegmentationSpecialCases(ors_service)
        self.route_calculator = SegmentRouteCalculator(ors_service)
        self.route_assembler = RouteAssembler()
        
        # Nouveaux modules pour la stratégie hybride
        self.tollways_analyzer = TollwaysAnalyzer()
        self.hybrid_segmenter = HybridSegmenter(self.ors, self.exit_optimizer)
    
    def find_route_with_exact_tolls(
        self, 
        coordinates: List[List[float]], 
        target_tolls: int
    ) -> Optional[Dict]:
        """
        Trouve une route avec exactement le nombre de péages demandé.
        Utilise la stratégie hybride tollways + optimisation.
        """
        with performance_tracker.measure_operation("intelligent_segmentation_v3"):
            print(f"🧠 Segmentation Hybride V3 : {target_tolls} péage(s) exact(s)")
            
            # CAS SPÉCIAL : 0 péage demandé
            if target_tolls == 0:
                print("🚫 Cas spécial : 0 péage demandé")
                return self.special_cases.get_toll_free_route(coordinates)
            
            # Étape 1 : Route de base + segments tollways
            base_route, tollways_data = self._get_base_route_with_tollways(coordinates)
            if not base_route:
                return None
            
            # Étape 2 : Identifier péages SUR la route
            route_coords = RouteUtils.extract_route_coordinates(base_route)
            tolls_on_route = self._identify_tolls_on_base_route(route_coords)
            
            # CAS SPÉCIAUX : optimisations directes
            if len(tolls_on_route) < target_tolls:
                print(f"⚠️ Pas assez de péages ({len(tolls_on_route)} < {target_tolls})")
                return self.special_cases.format_base_route_as_result(base_route)
            
            if len(tolls_on_route) == target_tolls:
                print(f"✅ Nombre exact de péages trouvé")
                return self.special_cases.format_base_route_as_result(base_route)
            
            # Étape 3 : Sélectionner péages cibles
            selected_tolls = self._select_target_tolls(tolls_on_route, target_tolls)
            if not selected_tolls:
                return None
            
            # Étape 4 : **NOUVEAU** Segmentation hybride
            print("🏗️ Étape 4 : Segmentation hybride tollways + optimisation...")
            segments = self.hybrid_segmenter.create_hybrid_segments(
                coordinates, tollways_data, tolls_on_route, selected_tolls, route_coords
            )
            
            if not segments:
                print("❌ Échec segmentation hybride, fallback route de base")
                return self.special_cases.format_base_route_as_result(base_route)
            
            # Étape 5 : Calcul des routes
            print("📍 Étape 5 : Calcul des routes pour chaque segment...")
            segment_routes = self.route_calculator.calculate_all_segments(segments)
            
            if not segment_routes:
                print("❌ Échec calcul segments, fallback route de base")
                return self.special_cases.format_base_route_as_result(base_route)
            
            # Étape 6 : Assemblage final
            print("🔧 Étape 6 : Assemblage final...")
            return self.route_assembler.assemble_final_route_multi(
                segment_routes, target_tolls, selected_tolls
            )
    
    def _get_base_route_with_tollways(self, coordinates: List[List[float]]) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Étape 1 : Route de base + extraction des segments tollways."""
        try:
            print(f"🛣️ Étape 1 : Route de base + tollways {coordinates[0]} → {coordinates[1]}")
            base_route = self.ors.get_base_route(coordinates, include_tollways=True)
            
            if not base_route:
                return None, None
            
            # Extraire les données tollways
            tollways_data = self._extract_tollways_data(base_route)
            print(f"   📊 {len(tollways_data.get('segments', []))} segments tollways détectés")
            
            return base_route, tollways_data
            
        except Exception as e:
            print(f"❌ Erreur route de base : {e}")
            return None, None
    
    def _extract_tollways_data(self, base_route: Dict) -> Dict:
        """Extrait les données tollways de la réponse ORS."""
        try:
            features = base_route.get('features', [])
            if not features:
                return {'segments': []}
            
            properties = features[0].get('properties', {})
            extras = properties.get('extras', {})
            tollways = extras.get('tollways', {})
            
            if 'values' not in tollways:
                return {'segments': []}
            
            # Transformer en format plus utilisable
            segments = []
            for value in tollways['values']:
                if len(value) >= 3:
                    segments.append({
                        'start_waypoint': value[0],
                        'end_waypoint': value[1],
                        'is_toll': value[2] == 1,
                        'is_free': value[2] == 0
                    })
            
            return {
                'segments': segments,
                'route_coords': RouteUtils.extract_route_coordinates(base_route)
            }
            
        except Exception as e:
            print(f"⚠️ Erreur extraction tollways : {e}")
            return {'segments': []}
    
    def _identify_tolls_on_base_route(self, route_coords: List[List[float]]) -> List[MatchedToll]:
        """Étape 2 : Identifier péages SUR la route (réutilise la logique V2)."""
        print("🔍 Étape 2 : Identification des péages sur la route...")
        
        # Recherche large + stricte (même logique que V2)
        osm_tolls_large = self.osm_parser.find_tolls_near_route(route_coords, max_distance_km=0.5)
        print(f"   📍 Détection large : {len(osm_tolls_large)} péages dans 500m")
        
        tolls_on_route_strict = filter_tolls_on_route_strict(
            osm_tolls_large, route_coords, max_distance_m=1, coordinate_attr='coordinates', verbose=True
        )
        
        osm_tolls_strict = [toll_data[0] for toll_data in tolls_on_route_strict]
        print(f"   🎯 {len(osm_tolls_strict)} péages strictement sur la route")
        
        # Convertir, matcher, dédupliquer, ordonner
        osm_tolls_formatted = convert_osm_tolls_to_matched_format(osm_tolls_strict)
        matched_tolls = self.toll_matcher.match_osm_tolls_with_csv(osm_tolls_formatted, max_distance_km=2.0)
        deduplicated_tolls = TollDeduplicator.deduplicate_tolls_by_proximity(matched_tolls, route_coords)
        ordered_tolls = TollDeduplicator.sort_tolls_by_route_position(deduplicated_tolls, route_coords)
        
        return ordered_tolls
    
    def _select_target_tolls(self, available_tolls: List[MatchedToll], target_count: int) -> List[MatchedToll]:
        """Étape 3 : Sélection de péages (réutilise la logique V2)."""
        print(f"🎯 Étape 3 : Sélection de {target_count} péage(s)...")
        
        if target_count > len(available_tolls):
            return []
        
        # Séparer par système
        open_tolls = [t for t in available_tolls if t.is_open_system]
        closed_tolls = [t for t in available_tolls if not t.is_open_system]
        
        # Logique de sélection (même que V2)
        selected_tolls = []
        
        # Prioriser fermés par paires
        if len(closed_tolls) >= 2:
            pairs_available = len(closed_tolls) // 2
            pairs_needed = min(pairs_available, target_count // 2)
            if target_count % 2 == 1 and pairs_available > pairs_needed:
                pairs_needed += 1
            selected_tolls.extend(closed_tolls[:pairs_needed * 2])
        
        # Compléter avec ouverts
        remaining = target_count - len(selected_tolls)
        if remaining > 0:
            selected_tolls.extend(open_tolls[:remaining])
        
        final_selected = selected_tolls[:target_count]
        
        # Vérifier contrainte (pas de fermé seul)
        closed_count = sum(1 for t in final_selected if not t.is_open_system)
        if closed_count == 1:
            final_selected = open_tolls[:target_count]
        
        print(f"   ✅ {len(final_selected)} péages sélectionnés")
        return final_selected


class TollwaysAnalyzer:
    """Analyse les segments tollways pour identifier les cas de segmentation."""
    
    def analyze_segments_for_tolls(self, tollways_segments: List[Dict], tolls_on_route: List[MatchedToll], route_coords: List[List[float]]) -> Dict:
        """
        Analyse les segments tollways pour identifier où sont les péages.
        
        Returns:
            Dict contenant l'analyse des segments et péages
        """
        print("🔍 Analyse des segments tollways vs péages...")
        
        analysis = {
            'segments_with_tolls': [],
            'free_segments': [],
            'multi_toll_segments': [],
            'single_toll_segments': []
        }
        
        for i, segment in enumerate(tollways_segments):
            if segment['is_toll']:
                # Trouver quels péages sont dans ce segment
                tolls_in_segment = self._find_tolls_in_segment(segment, tolls_on_route, route_coords)
                
                segment_info = {
                    'index': i,
                    'segment': segment,
                    'tolls': tolls_in_segment,
                    'toll_count': len(tolls_in_segment)
                }
                
                analysis['segments_with_tolls'].append(segment_info)
                
                if len(tolls_in_segment) > 1:
                    analysis['multi_toll_segments'].append(segment_info)
                    print(f"   ⚠️ Segment {i}: {len(tolls_in_segment)} péages (multi-péage)")
                else:
                    analysis['single_toll_segments'].append(segment_info)
                    print(f"   ✅ Segment {i}: 1 péage (normal)")
            else:
                analysis['free_segments'].append({
                    'index': i,
                    'segment': segment
                })
                print(f"   🆓 Segment {i}: gratuit")
        
        return analysis
    
    def _find_tolls_in_segment(self, segment: Dict, tolls: List[MatchedToll], route_coords: List[List[float]]) -> List[MatchedToll]:
        """Trouve quels péages sont dans un segment donné."""
        segment_coords = route_coords[segment['start_waypoint']:segment['end_waypoint']+1]
        if len(segment_coords) < 2:
            return []
        
        tolls_in_segment = []
        for toll in tolls:
            toll_coords = toll.osm_coordinates or toll.csv_coordinates
            if toll_coords and self._is_toll_in_segment_coords(toll_coords, segment_coords):
                tolls_in_segment.append(toll)
        
        return tolls_in_segment
    
    def _is_toll_in_segment_coords(self, toll_coords: List[float], segment_coords: List[List[float]]) -> bool:
        """Vérifie si un péage est dans les coordonnées d'un segment."""
        # Approximation simple : vérifier si le péage est dans la bbox du segment
        if len(segment_coords) < 2:
            return False
        
        lons = [coord[0] for coord in segment_coords]
        lats = [coord[1] for coord in segment_coords]
        
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)
        
        return (min_lon <= toll_coords[0] <= max_lon and 
                min_lat <= toll_coords[1] <= max_lat)


class HybridSegmenter:
    """Crée les segments en utilisant la stratégie hybride."""
    
    def __init__(self, ors_service, exit_optimizer: ExitOptimizationManager):
        self.ors = ors_service
        self.exit_optimizer = exit_optimizer
        self.tollways_analyzer = TollwaysAnalyzer()
    
    def create_hybrid_segments(
        self, 
        coordinates: List[List[float]], 
        tollways_data: Dict, 
        tolls_on_route: List[MatchedToll], 
        selected_tolls: List[MatchedToll],
        route_coords: List[List[float]]
    ) -> List[Dict]:
        """
        Crée les segments en utilisant la stratégie hybride.
        
        Logique :
        1. Analyser les segments tollways vs péages
        2. Utiliser segmentation naturelle pour segments simples
        3. Optimisation de sortie pour segments multi-péages
        """
        print("🔧 Création des segments hybrides...")
        
        tollways_segments = tollways_data.get('segments', [])
        if not tollways_segments:
            print("⚠️ Pas de segments tollways, fallback segmentation classique")
            return self._fallback_segments(coordinates, selected_tolls)
        
        # Analyser les segments
        analysis = self.tollways_analyzer.analyze_segments_for_tolls(
            tollways_segments, tolls_on_route, route_coords
        )
        
        # Identifier les péages à éviter
        tolls_to_avoid = [t for t in tolls_on_route if t not in selected_tolls]
        
        # Créer les segments hybrides
        segments = self._create_segments_from_analysis(
            coordinates, analysis, selected_tolls, tolls_to_avoid, route_coords
        )
        
        return segments
    
    def _create_segments_from_analysis(
        self, 
        coordinates: List[List[float]], 
        analysis: Dict, 
        selected_tolls: List[MatchedToll], 
        tolls_to_avoid: List[MatchedToll],
        route_coords: List[List[float]]
    ) -> List[Dict]:
        """Crée les segments basés sur l'analyse."""
        segments = []
        current_start = coordinates[0]
        
        # Pour chaque segment avec péages à éviter
        for segment_info in analysis['segments_with_tolls']:
            segment = segment_info['segment']
            tolls_in_segment = segment_info['tolls']
            
            # Vérifier si on doit éviter des péages dans ce segment
            tolls_to_avoid_in_segment = [t for t in tolls_in_segment if t in tolls_to_avoid]
            
            if tolls_to_avoid_in_segment:
                print(f"   🚫 Évitement nécessaire dans segment {segment_info['index']}")
                
                if len(tolls_in_segment) == 1:
                    # Cas simple : utiliser fin de segment gratuit précédent
                    segment_end = self._get_segment_end_coords(segment, route_coords)
                    segments.append({
                        'start': current_start,
                        'end': segment_end,
                        'type': 'avoid_tolls',
                        'description': f"Évitement segment {segment_info['index']}"
                    })
                    current_start = segment_end
                else:
                    # Cas complexe : optimisation de sortie nécessaire
                    print(f"   ⚙️ Optimisation de sortie pour segment multi-péages")
                    opt_segments = self._handle_multi_toll_segment(
                        current_start, segment_info, selected_tolls, tolls_to_avoid_in_segment, route_coords
                    )
                    segments.extend(opt_segments)
                    if opt_segments:
                        current_start = opt_segments[-1]['end']
        
        # Segment final vers destination
        if current_start != coordinates[1]:
            segments.append({
                'start': current_start,
                'end': coordinates[1],
                'type': 'final',
                'description': 'Segment final'
            })
        
        return segments
    
    def _get_segment_end_coords(self, segment: Dict, route_coords: List[List[float]]) -> List[float]:
        """Récupère les coordonnées de fin d'un segment."""
        end_waypoint = segment['end_waypoint']
        if end_waypoint < len(route_coords):
            return route_coords[end_waypoint]
        return route_coords[-1]
    
    def _handle_multi_toll_segment(
        self, 
        start_coords: List[float], 
        segment_info: Dict, 
        selected_tolls: List[MatchedToll], 
        tolls_to_avoid: List[MatchedToll],
        route_coords: List[List[float]]
    ) -> List[Dict]:
        """Gère un segment avec plusieurs péages via optimisation de sortie."""
        # Trouver le péage sélectionné dans ce segment
        selected_in_segment = [t for t in segment_info['tolls'] if t in selected_tolls]
        
        if not selected_in_segment:
            # Aucun péage sélectionné dans ce segment, éviter complètement
            segment_end = self._get_segment_end_coords(segment_info['segment'], route_coords)
            return [{
                'start': start_coords,
                'end': segment_end,
                'type': 'avoid_tolls',
                'description': f"Évitement complet segment {segment_info['index']}"
            }]
        
        # Optimiser le péage sélectionné pour éviter les autres
        toll_to_optimize = selected_in_segment[0]
        remaining_tolls = [t for t in segment_info['tolls'] if t != toll_to_optimize]
        
        # Utiliser l'optimisation de sortie
        optimized_toll = self.exit_optimizer.optimize_toll_exit(
            toll_to_optimize, remaining_tolls, start_coords, None, route_coords
        )
        
        if optimized_toll:
            # Utiliser la sortie optimisée
            exit_coords = optimized_toll.osm_coordinates or optimized_toll.csv_coordinates
            return [
                {
                    'start': start_coords,
                    'end': exit_coords,
                    'type': 'to_optimized_exit',
                    'description': f'Vers sortie optimisée {optimized_toll.effective_name}'
                }
            ]
        else:
            # Fallback : éviter le segment complètement
            segment_end = self._get_segment_end_coords(segment_info['segment'], route_coords)
            return [{
                'start': start_coords,
                'end': segment_end,
                'type': 'avoid_tolls',
                'description': f"Fallback évitement segment {segment_info['index']}"
            }]
    
    def _fallback_segments(self, coordinates: List[List[float]], selected_tolls: List[MatchedToll]) -> List[Dict]:
        """Segmentation de fallback classique."""
        return [{
            'start': coordinates[0],
            'end': coordinates[1],
            'type': 'direct',
            'description': 'Route directe (fallback)'
        }]
