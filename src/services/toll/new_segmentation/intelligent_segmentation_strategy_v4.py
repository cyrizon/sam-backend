"""
intelligent_segmentation_strategy_v4.py
--------------------------------------

Stratégie hybride complète : utilisation des segments tollways d'ORS + optimisation de sortie en fallback.

Algorithme optimisé :
1. Route de base + extraction des segments tollways avec coordonnées
2. Identifier péages SUR la route  
3. Sélectionner X péages selon contraintes
4. **HYBRIDE** : Segmentation basée sur tollways + optimisation ciblée
   - Cas normal : Utiliser segments gratuits naturels
   - Cas complexe : Optimiser sorties pour péages problématiques
5. Calcul des routes pour chaque segment
6. Assemblage final

Règles respectées :
- Fichier < 350 lignes
- Une responsabilité par classe/fonction
- Réutilisation de code existant
- Organisation modulaire
"""

from typing import List, Dict, Optional, Tuple
from src.services.toll.new_segmentation.intelligent_segmentation_helpers import SegmentationSpecialCases, RouteUtils
from src.services.toll.new_segmentation.toll_matcher import TollMatcher, MatchedToll, convert_osm_tolls_to_matched_format
from src.services.toll.new_segmentation.toll_deduplicator import TollDeduplicator
from src.services.toll.new_segmentation.polyline_intersection import filter_tolls_on_route_strict
from src.services.toll.new_segmentation.exit_optimization import ExitOptimizationManager
from src.services.toll.new_segmentation.segment_route_calculator import SegmentRouteCalculator
from src.services.toll.new_segmentation.route_assembler import RouteAssembler
from src.services.toll.new_segmentation.hybrid_strategy import HybridSegmenter
from benchmark.performance_tracker import performance_tracker
from src.services.osm_data_cache import osm_data_cache


class IntelligentSegmentationStrategyV4:
    """
    Stratégie hybride tollways + optimisation de sortie.
    Version optimisée et modulaire.
    """
    
    def __init__(self, ors_service, osm_data_file: str = None):
        """Initialise la stratégie hybride optimisée."""
        self.ors = ors_service
        self.osm_parser = osm_data_cache._osm_parser
        self.toll_matcher = TollMatcher()
        
        # Modules spécialisés
        self.exit_optimizer = ExitOptimizationManager(self.osm_parser, self.toll_matcher, self.ors)
        self.special_cases = SegmentationSpecialCases(ors_service)
        self.route_calculator = SegmentRouteCalculator(ors_service)
        self.route_assembler = RouteAssembler()
        self.hybrid_segmenter = HybridSegmenter(ors_service, self.exit_optimizer, self.osm_parser)
    
    def find_route_with_exact_tolls(
        self, 
        coordinates: List[List[float]], 
        target_tolls: int
    ) -> Optional[Dict]:
        """
        Trouve une route avec exactement le nombre de péages demandé.
        Utilise la stratégie hybride tollways + optimisation.
        """
        with performance_tracker.measure_operation("intelligent_segmentation_v4"):
            print(f"🧠 Segmentation Hybride V4 : {target_tolls} péage(s) exact(s)")
            
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
            
            # Étape 4 : **HYBRIDE** Segmentation tollways + optimisation
            print("🏗️ Étape 4 : Segmentation hybride tollways + optimisation...")
            segments = self.hybrid_segmenter.create_hybrid_segments(
                coordinates, tollways_data, tolls_on_route, selected_tolls, route_coords
            )
            
            if not segments:
                print("❌ Échec segmentation hybride, fallback route de base")
                return self.special_cases.format_base_route_as_result(base_route)
            
            # Étape 5 : Calcul des routes
            print("📍 Étape 5 : Calcul des routes pour chaque segment...")
            segment_routes = self._calculate_hybrid_segments(segments)
            
            if not segment_routes:
                print("❌ Échec calcul segments, fallback route de base")
                return self.special_cases.format_base_route_as_result(base_route)
            
            

            # Étape 6 : Assemblage final
            print("🔧 Étape 6 : Assemblage final...")
            return self.route_assembler.assemble_final_route_multi(
                segment_routes, target_tolls, selected_tolls
            )
    
    def _get_base_route_with_tollways(self, coordinates: List[List[float]]) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Étape 1 : Route de base + extraction des segments tollways avec coordonnées."""
        try:
            print(f"🛣️ Étape 1 : Route de base + tollways {coordinates[0]} → {coordinates[1]}")
            base_route = self.ors.get_base_route(coordinates, include_tollways=True)
            
            if not base_route:
                return None, None
            
            # Extraire les données tollways avec coordonnées
            tollways_data = self._extract_tollways_with_coordinates(base_route)
            print(f"   📊 {len(tollways_data.get('segments', []))} segments tollways avec coordonnées")
            
            return base_route, tollways_data
            
        except Exception as e:
            print(f"❌ Erreur route de base : {e}")
            return None, None
    
    def _extract_tollways_with_coordinates(self, base_route: Dict) -> Dict:
        """Extrait les segments tollways avec leurs coordonnées de début/fin."""
        try:
            features = base_route.get('features', [])
            if not features:
                return {'segments': []}
            
            properties = features[0].get('properties', {})
            extras = properties.get('extras', {})
            tollways = extras.get('tollways', {})
            
            if 'values' not in tollways:
                return {'segments': []}
            
            # Récupérer les coordonnées de la route
            route_coords = RouteUtils.extract_route_coordinates(base_route)
            
            # Transformer en format avec coordonnées
            segments = []
            for value in tollways['values']:
                if len(value) >= 3:
                    start_waypoint = value[0]
                    end_waypoint = value[1]
                    is_toll = value[2] == 1
                    
                    # Récupérer les coordonnées correspondantes
                    start_coord = route_coords[start_waypoint] if start_waypoint < len(route_coords) else None
                    end_coord = route_coords[end_waypoint] if end_waypoint < len(route_coords) else None
                    
                    segments.append({
                        'start_waypoint': start_waypoint,
                        'end_waypoint': end_waypoint,
                        'start_coord': start_coord,
                        'end_coord': end_coord,
                        'is_toll': is_toll,
                        'is_free': not is_toll,
                        'coordinates': route_coords[start_waypoint:end_waypoint + 1] if end_waypoint < len(route_coords) else []
                    })
            
            return {
                'segments': segments,
                'route_coords': route_coords
            }
            
        except Exception as e:
            print(f"⚠️ Erreur extraction tollways : {e}")
            return {'segments': []}
    
    def _identify_tolls_on_base_route(self, route_coords: List[List[float]]) -> List[MatchedToll]:
        """Étape 2 : Identifier péages SUR la route (réutilise la logique éprouvée)."""
        print("🔍 Étape 2 : Identification des péages sur la route...")
        
        # Recherche large + stricte (logique V2/V3 éprouvée)
        osm_tolls_large = self.osm_parser.find_tolls_near_route(route_coords, max_distance_km=0.5)
        print(f"   📍 Détection large : {len(osm_tolls_large)} péages dans 500m")
        
        tolls_on_route_strict = filter_tolls_on_route_strict(
            osm_tolls_large, route_coords, max_distance_m=1, coordinate_attr='coordinates', verbose=True
        )
        
        osm_tolls_strict = [toll_data[0] for toll_data in tolls_on_route_strict]
        print(f"   🎯 {len(osm_tolls_strict)} péages strictement sur la route")
        
        # Convertir, matcher, dédupliquer, ordonner (logique éprouvée)
        osm_tolls_formatted = convert_osm_tolls_to_matched_format(osm_tolls_strict)
        matched_tolls = self.toll_matcher.match_osm_tolls_with_csv(osm_tolls_formatted, max_distance_km=2.0)
        deduplicated_tolls = TollDeduplicator.deduplicate_tolls_by_proximity(matched_tolls, route_coords)
        ordered_tolls = TollDeduplicator.sort_tolls_by_route_position(deduplicated_tolls, route_coords)
        
        return ordered_tolls
    
    def _select_target_tolls(self, available_tolls: List[MatchedToll], target_count: int) -> List[MatchedToll]:
        """Étape 3 : Sélection de péages (réutilise la logique V2/V3)."""
        print(f"🎯 Étape 3 : Sélection de {target_count} péage(s)...")
        
        if target_count > len(available_tolls):
            return []
        
        # Séparer par système
        open_tolls = [t for t in available_tolls if t.is_open_system]
        closed_tolls = [t for t in available_tolls if not t.is_open_system]
        
        # Logique de sélection éprouvée
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
    
    def _calculate_hybrid_segments(self, segments: List[Dict]) -> List[Dict]:
        """Calcule les routes pour les segments hybrides."""
        print(f"🔢 Calcul de {len(segments)} segments hybrides...")
        
        segment_routes = []
        
        for i, segment in enumerate(segments):
            print(f"\n📍 Segment {i+1}/{len(segments)}")
            
            segment_type = segment.get('type', 'normal')
            start_coord = segment['start']
            end_coord = segment['end']
            description = segment.get('description', f'Segment {i+1}')
            
            print(f"🔄 Calcul segment : {description}")
            print(f"   📍 Départ: {start_coord}")
            print(f"   📍 Arrivée: {end_coord}")
            
            # Debug : Afficher les clés et coordonnées des segments
            for idx, seg in enumerate(segments):
                start = seg.get('start')
                end = seg.get('end')
                print(f"   [DEBUG] Segment {idx+1}: keys={list(seg.keys())}, start={start}, end={end}")
            
            # Calculer selon le type de segment
            if segment_type == 'toll_free':
                route = self.ors.get_base_route([start_coord, end_coord], include_tollways=False)
                print(f"   🚫 Route sans péage calculée")
            else:
                route = self.ors.get_base_route([start_coord, end_coord], include_tollways=True)
                print(f"   🛣️ Route normale calculée")
            
            if route:
                segment_routes.append({
                    'segment_info': segment,
                    'route': route,
                    'index': i
                })
                print(f"   ✅ Segment calculé avec succès")
            else:
                print(f"   ❌ Échec calcul segment {i+1}")
                return []
        
        print(f"✅ {len(segment_routes)} segments calculés avec succès")
        return segment_routes
