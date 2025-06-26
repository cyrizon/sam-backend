"""
intelligent_segmentation_v2_optimized.py
---------------------------------------

Version optimisée de la stratégie de segmentation intelligente V2.
S'inspire des performances de la V3/V4 en travaillant sur les segments tollways d'ORS.

OPTIMISATIONS CLÉS :
1. Travail sur les segments tollways (comme V3/V4) plutôt que route complète
2. Matching péages OSM/CSV au chargement pour éviter le re-matching à chaque requête
3. Utilisation des motorway_junctions + motorway_links liés (pas de recherche géographique)
4. Attribut csv_role disponible dès le chargement pour chaque péage
5. Logique segments gratuits : pas d'usage entre deux péages fermés
6. Pré-calcul des associations péages-segments pour performance

Algorithme optimisé :
1. Route de base + extraction segments tollways
2. Identification péages SUR segments (pré-matchés)
3. Sélection péages cibles (prioriser système ouvert)
4. Segmentation intelligente basée sur tollways
5. Calcul des routes pour chaque segment
6. Assemblage final optimisé
"""

from typing import List, Dict, Optional, Tuple
from .toll_segment_builder import TollSegmentBuilder
from .segment_route_calculator import SegmentRouteCalculator
from .toll_matcher import TollMatcher, MatchedToll, convert_osm_tolls_to_matched_format
from .toll_deduplicator import TollDeduplicator
from .intelligent_segmentation_helpers import SegmentationSpecialCases, RouteUtils
from .route_assembler import RouteAssembler
from .polyline_intersection import filter_tolls_on_route_strict
from .hybrid_strategy.tollways_analyzer import TollwaysAnalyzer
from .hybrid_strategy.segment_avoidance_manager import SegmentAvoidanceManager
from benchmark.performance_tracker import performance_tracker
from src.services.osm_data_cache import osm_data_cache


class IntelligentSegmentationStrategyV2Optimized:
    """
    Version optimisée de la stratégie de segmentation intelligente V2.
    Travaille sur les segments tollways avec péages pré-matchés.
    """
    
    def __init__(self, ors_service, osm_data_file: str = None):
        """
        Initialise la stratégie optimisée.
        
        Args:
            ors_service: Service ORS pour les calculs de routes
            osm_data_file: (ignoré, conservé pour compatibilité)
        """
        self.ors = ors_service
        self.osm_parser = osm_data_cache._osm_parser
        
        # Modules core
        self.toll_matcher = TollMatcher()
        # Note: TollDeduplicator utilisé comme méthode statique
        self.special_cases = SegmentationSpecialCases(ors_service)
        self.route_calculator = SegmentRouteCalculator(ors_service)
        self.route_assembler = RouteAssembler()
        
        # Modules optimisés pour tollways
        self.tollways_analyzer = TollwaysAnalyzer()
        self.avoidance_manager = SegmentAvoidanceManager(ors_service, self.osm_parser)
        
        # Cache pour les péages pré-matchés par segment
        self._segment_tolls_cache = {}
        
        print("🚀 Stratégie V2 Optimisée initialisée (segments tollways + péages pré-matchés)")
    
    def find_route_with_exact_tolls(
        self, 
        coordinates: List[List[float]], 
        target_tolls: int
    ) -> Optional[Dict]:
        """
        Trouve une route avec exactement le nombre de péages demandé.
        Utilise la stratégie optimisée avec segments tollways.
        """
        with performance_tracker.measure_operation("intelligent_segmentation_v2_optimized"):
            print(f"🧠 Segmentation V2 Optimisée : {target_tolls} péage(s) exact(s)")
            
            # CAS SPÉCIAL : 0 péage demandé
            if target_tolls == 0:
                print("🚫 Cas spécial : 0 péage demandé")
                return self.special_cases.get_toll_free_route(coordinates)
            
            # Étape 1 : Route de base + segments tollways
            base_route_response, tollways_data = self._get_base_route_with_tollways(coordinates)
            if not base_route_response:
                return None
            
            # Étape 2 : Identifier péages pré-matchés SUR les segments
            route_coords = RouteUtils.extract_route_coordinates(base_route_response)
            tolls_on_segments = self._identify_prematched_tolls_on_segments(
                tollways_data['segments'], route_coords
            )
            
            # CAS SPÉCIAUX : optimisations directes
            if len(tolls_on_segments) < target_tolls:
                print(f"⚠️ Pas assez de péages ({len(tolls_on_segments)} < {target_tolls})")
                return self.special_cases.format_base_route_as_result(base_route_response)
            
            if len(tolls_on_segments) == target_tolls:
                print(f"✅ Nombre exact de péages trouvé")
                return self.special_cases.format_base_route_as_result(base_route_response)
            
            # Étape 3 : Sélectionner péages cibles (prioriser système ouvert)
            selected_tolls = self._select_target_tolls_optimized(tolls_on_segments, target_tolls)
            if not selected_tolls:
                return None
            
            # Étape 4 : Segmentation intelligente basée sur tollways
            print("🏗️ Étape 4 : Segmentation intelligente optimisée...")
            segments = self._create_optimized_segments(
                coordinates, tollways_data, tolls_on_segments, selected_tolls, route_coords
            )
            
            if not segments:
                print("❌ Échec segmentation optimisée, fallback route de base")
                return self.special_cases.format_base_route_as_result(base_route_response)
            
            # Étape 5 : Calcul des routes pour chaque segment
            print("🛣️ Étape 5 : Calcul des routes par segment...")
            calculated_segments = self._calculate_segments_routes(segments, base_route_response, tollways_data)
            
            if not calculated_segments:
                print("❌ Échec calcul des segments")
                return self.special_cases.format_base_route_as_result(base_route_response)
            
            # Étape 6 : Assemblage final optimisé
            print("🔧 Étape 6 : Assemblage final optimisé...")
            final_route = self.route_assembler.assemble_final_route_multi(
                calculated_segments, target_tolls, selected_tolls
            )
            
            if not final_route:
                print("❌ Échec assemblage final")
                return self.special_cases.format_base_route_as_result(base_route_response)
            
            print("✅ Segmentation V2 Optimisée réussie")
            return final_route
    
    def _get_base_route_with_tollways(self, coordinates: List[List[float]]) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Obtient la route de base avec les segments tollways.
        
        Returns:
            Tuple[route_response, tollways_data]: Réponse ORS complète et données tollways
        """
        print("🛣️ Étape 1 : Route de base + segments tollways...")

        response = self.ors.get_base_route(coordinates, include_tollways=True)
        if not response or "features" not in response or not response["features"]:
            print("❌ Échec obtention route de base")
            return None, None

        base_feature = response["features"][0]
        properties = base_feature.get("properties", {})

        # Extraire segments tollways à partir des propriétés
        tollways_data = self._extract_tollways_segments(properties)
        if not tollways_data:
            print("⚠️ Aucun segment tollway trouvé")
            return response, {'segments': []}

        print(f"✅ Route de base obtenue avec {len(tollways_data['segments'])} segments tollways")
        return response, tollways_data

    def _extract_tollways_segments(self, properties: Dict) -> Optional[Dict]:
        """
        Extrait les segments tollways à partir des propriétés d'une feature ORS.
        """
        extras = properties.get('extras', {})
        tollways_info = extras.get('tollways', {})
        if not tollways_info:
            return None
        segments = []
        values = tollways_info.get('values', [])
        for segment_info in values:
            if len(segment_info) >= 3:
                start_idx, end_idx, is_toll = segment_info
                segment = {
                    'start_waypoint': start_idx,
                    'end_waypoint': end_idx,
                    'is_toll': bool(is_toll),
                    'segment_type': 'toll' if is_toll else 'free'
                }
                segments.append(segment)
        return {
            'segments': segments,
            'total_segments': len(segments),
            'toll_segments': sum(1 for s in segments if s['is_toll']),
            'free_segments': sum(1 for s in segments if not s['is_toll'])
        }
    
    def _identify_prematched_tolls_on_segments(
        self, 
        segments: List[Dict], 
        route_coords: List[List[float]]
    ) -> List[MatchedToll]:
        """
        Identifie les péages pré-matchés sur les segments tollways.
        
        OPTIMISATION CLÉ : Utilise les péages déjà matchés OSM/CSV au chargement,
        évite le re-matching à chaque requête.
        
        Args:
            segments: Segments tollways extraits
            route_coords: Coordonnées de la route
            
        Returns:
            List[MatchedToll]: Péages pré-matchés trouvés sur les segments
        """
        print("🔍 Étape 2 : Identification péages pré-matchés sur segments...")
        
        # Récupérer les péages pré-matchés du cache OSM
        prematched_tolls = self._get_prematched_tolls_from_cache()
        
        if not prematched_tolls:
            print("⚠️ Aucun péage pré-matché disponible, fallback sur matching traditionnel")
            return self._fallback_traditional_matching(route_coords)
        
        # Filtrer les péages qui sont VRAIMENT sur la route (tous segments)
        # Utiliser une détection stricte comme dans la V2 originale
        tolls_on_segments = []

        for segment in segments:
            print(f"   Segment {segment['start_waypoint']} à {segment['end_waypoint']} (toll: {segment['is_toll']})")
            
            # Extraire les coordonnées du segment
            start_idx = segment['start_waypoint']
            end_idx = segment['end_waypoint']
            
            if end_idx >= len(route_coords):
                continue
            
            segment_coords = route_coords[start_idx:end_idx + 1]
            
            # Trouver les péages pré-matchés sur ce segment (tous segments, pas seulement payants)
            segment_tolls = self._find_prematched_tolls_on_segment(
                prematched_tolls, segment_coords
            )
            
            tolls_on_segments.extend(segment_tolls)
        
        # Filtrage strict : garder seulement les péages à moins de 1m de la route
        print("🎯 Filtrage strict des péages (distance < 1m)...")
        strict_tolls = []
        for toll in tolls_on_segments:
            min_distance_m = float('inf')
            for coord in route_coords:
                dist_m = self._calculate_distance_meters(
                    [toll.osm_coordinates[1], toll.osm_coordinates[0]], 
                    [coord[1], coord[0]]
                )
                min_distance_m = min(min_distance_m, dist_m)
            
            if min_distance_m <= 1.0:  # 1m max
                strict_tolls.append(toll)
                print(f"   ✅ {toll.effective_name} : {min_distance_m:.1f}m")
            else:
                print(f"   ❌ {toll.effective_name} : {min_distance_m:.1f}m (trop loin)")
        
        tolls_on_segments = strict_tolls
        
        # Déduplication par proximité (méthode statique)
        tolls_on_segments = TollDeduplicator.deduplicate_tolls_by_proximity(tolls_on_segments, route_coords)
        
        print(f"✅ {len(tolls_on_segments)} péages pré-matchés trouvés sur segments")
        
        # Debug : afficher les péages avec leur csv_role
        for toll in tolls_on_segments:
            role_str = f"({toll.csv_role})" if toll.csv_role else "(non-matché)"
            print(f"   🏷️ {toll.effective_name} {role_str}")
        
        return tolls_on_segments
    
    def _get_prematched_tolls_from_cache(self) -> List[MatchedToll]:
        """
        Récupère les péages pré-matchés du cache OSM.
        
        OPTIMISATION : Les péages sont matchés OSM/CSV au chargement des données,
        pas à chaque requête.
        
        Returns:
            List[MatchedToll]: Péages pré-matchés avec csv_role disponible
        """
        if not self.osm_parser or not hasattr(self.osm_parser, 'toll_stations'):
            return []
        
        prematched_tolls = []
        
        for toll_station in self.osm_parser.toll_stations:
            # Vérifier si le péage a été pré-matché avec les données CSV
            if hasattr(toll_station, 'csv_match') and toll_station.csv_match:
                # Péage pré-matché
                matched_toll = MatchedToll(
                    osm_id=toll_station.feature_id,
                    osm_name=toll_station.name,
                    osm_coordinates=toll_station.coordinates,
                    csv_id=toll_station.csv_match.get('id'),
                    csv_name=toll_station.csv_match.get('name'),
                    csv_role=toll_station.csv_match.get('role'),  # 'O' ou 'F'
                    csv_coordinates=toll_station.csv_match.get('coordinates'),
                    distance_m=toll_station.csv_match.get('distance_m', 0),
                    confidence=toll_station.csv_match.get('confidence', 1.0)
                )
                prematched_tolls.append(matched_toll)
            else:
                # Péage OSM non matché -> considéré comme fermé (csv_role='F')
                matched_toll = MatchedToll(
                    osm_id=toll_station.feature_id,
                    osm_name=toll_station.name,
                    osm_coordinates=toll_station.coordinates,
                    csv_id=None,
                    csv_name=None,
                    csv_role='F',  # Fermé par défaut si non matché
                    csv_coordinates=None,
                    distance_m=0,
                    confidence=0.0
                )
                prematched_tolls.append(matched_toll)
        
        return prematched_tolls
    
    def _find_prematched_tolls_on_segment(
        self, 
        prematched_tolls: List[MatchedToll], 
        segment_coords: List[List[float]]
    ) -> List[MatchedToll]:
        """
        Trouve les péages pré-matchés sur un segment donné.
        
        Args:
            prematched_tolls: Tous les péages pré-matchés
            segment_coords: Coordonnées du segment
            
        Returns:
            List[MatchedToll]: Péages trouvés sur ce segment
        """
        if not segment_coords:
            return []
        
        segment_tolls = []
        max_distance_km = 2.0  # Distance max pour considérer un péage sur le segment
        
        for toll in prematched_tolls:
            toll_coords = toll.osm_coordinates or toll.csv_coordinates
            if not toll_coords:
                continue
            
            # Calculer la distance minimale au segment
            min_distance = min(
                self._calculate_distance(toll_coords, point)
                for point in segment_coords
            )
            
            if min_distance <= max_distance_km:
                segment_tolls.append(toll)
        
        return segment_tolls
    
    def _fallback_traditional_matching(self, route_coords: List[List[float]]) -> List[MatchedToll]:
        """
        Fallback sur le matching traditionnel si les péages pré-matchés ne sont pas disponibles.
        
        Args:
            route_coords: Coordonnées de la route
            
        Returns:
            List[MatchedToll]: Péages matchés traditionnellement
        """
        print("🔄 Fallback matching traditionnel...")
        
        # Utiliser le système traditionnel de matching
        osm_tolls = filter_tolls_on_route_strict(
            self.osm_parser.toll_stations, route_coords, max_distance_km=5.0
        )
        
        if not osm_tolls:
            return []
        
        # Convertir au format MatchedToll
        osm_tolls_dict = convert_osm_tolls_to_matched_format(osm_tolls)
        
        # Matcher avec CSV
        matched_tolls = self.toll_matcher.match_osm_tolls_with_csv(osm_tolls_dict)
        
        return matched_tolls
    
    def _select_target_tolls_optimized(
        self, 
        tolls_on_segments: List[MatchedToll], 
        target_count: int
    ) -> List[MatchedToll]:
        """
        Sélectionne les péages cibles en priorisant le système fermé (comme l'ancienne V2).
        
        RÈGLES (identiques à l'ancienne V2) :
        - 1 péage : Seulement système ouvert (fermé seul = impossible)
        - 2+ péages : Priorité aux fermés (plus logique entrance→exit), puis ouverts
        - Contrainte : Jamais de péage fermé seul (toujours par paires minimum)
        
        Args:
            tolls_on_segments: Péages disponibles sur les segments
            target_count: Nombre de péages souhaités
            
        Returns:
            List[MatchedToll]: Péages sélectionnés
        """
        print(f"🎯 Étape 3 : Sélection {target_count} péages cibles (prioriser système fermé)...")
        
        if target_count > len(tolls_on_segments):
            print(f"❌ Pas assez de péages disponibles ({len(tolls_on_segments)} < {target_count})")
            return []
        
        if len(tolls_on_segments) <= target_count:
            return tolls_on_segments
        
        # Séparer par type de système (ouvert/fermé)
        open_system_tolls = [t for t in tolls_on_segments if t.csv_role == 'O']
        closed_system_tolls = [t for t in tolls_on_segments if t.csv_role != 'O']
        
        print(f"   � Disponibles : {len(open_system_tolls)} ouverts, {len(closed_system_tolls)} fermés")
        
        # Utiliser la logique unifiée de l'ancienne V2
        return self._select_tolls_unified_optimized(open_system_tolls, closed_system_tolls, target_count)
    
    def _select_tolls_unified_optimized(
        self, 
        open_tolls: List[MatchedToll], 
        closed_tolls: List[MatchedToll], 
        target_count: int
    ) -> List[MatchedToll]:
        """
        Logique unifiée de sélection de péages (identique à l'ancienne V2).
        
        Règles :
        1. Toujours prioriser les péages fermés (par paires)
        2. Si contrainte violée (1 seul fermé), passer aux ouverts
        3. Compléter avec les ouverts si nécessaire
        """
        selected_tolls = []
        
        # Étape 1 : Prendre d'abord les fermés (par paires si possible)
        if len(closed_tolls) >= 2:
            # Calculer combien de paires on peut prendre
            pairs_available = len(closed_tolls) // 2
            pairs_needed = min(pairs_available, target_count // 2)
            
            # Si target_count est impair et qu'on a assez de fermés, prendre une paire de plus
            if target_count % 2 == 1 and pairs_available > pairs_needed:
                pairs_needed += 1
            
            selected_tolls.extend(closed_tolls[:pairs_needed * 2])
        
        # Étape 2 : Compléter avec des ouverts si nécessaire
        remaining = target_count - len(selected_tolls)
        if remaining > 0:
            selected_tolls.extend(open_tolls[:remaining])
        
        # Étape 3 : Ajuster à la taille exacte
        final_selected = selected_tolls[:target_count]
        
        # Étape 4 : Vérifier la contrainte (pas de fermé seul, sauf si pas d'alternative)
        closed_count = sum(1 for t in final_selected if t.csv_role != 'O')
        if closed_count == 1 and len(open_tolls) > 0:
            print(f"   ⚠️ Contrainte violée : 1 seul fermé détecté, passage aux ouverts...")
            # Si on ne peut pas respecter la contrainte ET qu'on a des ouverts, prendre que des ouverts
            final_selected = open_tolls[:target_count]
        elif closed_count == 1 and len(open_tolls) == 0:
            print(f"   ✅ 1 seul fermé accepté (pas d'alternative ouverte)")
        
        print(f"   ✅ {len(final_selected)} péages sélectionnés : {[t.effective_name for t in final_selected]}")
        print(f"      - Fermés : {sum(1 for t in final_selected if t.csv_role != 'O')}")
        print(f"      - Ouverts : {sum(1 for t in final_selected if t.csv_role == 'O')}")
        
        return final_selected
    
    def _create_optimized_segments(
        self,
        coordinates: List[List[float]],
        tollways_data: Dict,
        tolls_on_segments: List[MatchedToll],
        selected_tolls: List[MatchedToll],
        route_coords: List[List[float]]
    ) -> List[Dict]:
        """
        Crée les segments optimisés basés sur l'analyse des tollways.
        
        LOGIQUE OPTIMISÉE :
        - Utilise les motorway_junctions + motorway_links liés
        - Pas de recherche géographique inutile
        - Segments gratuits : pas d'usage entre deux péages fermés
        
        Args:
            coordinates: [départ, arrivée]
            tollways_data: Données des segments tollways
            tolls_on_segments: Tous les péages sur segments
            selected_tolls: Péages sélectionnés
            route_coords: Coordonnées de la route
            
        Returns:
            List[Dict]: Segments optimisés
        """
        print("🏗️ Création segments optimisés...")
        
        print("\n🟦 DEBUG: Péages transmis à l'analyseur de segments (tous sur la route, <1m, après déduplication):")
        for t in tolls_on_segments:
            print(f"   - {t.effective_name} | {t.csv_role} | {t.osm_coordinates}")
        print(f"🟦 DEBUG: Péages sélectionnés (à utiliser): {[t.effective_name for t in selected_tolls]}")

        # Analyser les segments tollways vs TOUS les péages détectés sur la route
        analysis = self.tollways_analyzer.analyze_segments_for_tolls(
            tollways_data['segments'],
            tolls_on_segments,  # TOUS les péages détectés sur la route
            route_coords
        )
        
        # Identifier les segments à éviter
        segments_indices_to_avoid = self._identify_segments_to_avoid(analysis, selected_tolls)
        
        # Debug : afficher les indices à éviter
        for index in segments_indices_to_avoid:
            print(f"   📝 Segment {index} ajouté à la liste d'évitement")
        
        print(f"🎯 {len(segments_indices_to_avoid)} segments seront évités sur {len(segments_indices_to_avoid)} identifiés")
        
        # Créer les segments d'évitement avec logique optimisée
        avoidance_segments = self.avoidance_manager.create_avoidance_segments(
            tollways_data['segments'],
            segments_indices_to_avoid,  # Passer les indices directement
            route_coords,
            coordinates[0],
            coordinates[1]
        )
        
        # Optimiser l'assemblage final pour éviter les redondances
        optimized_segments = self._optimize_final_assembly(avoidance_segments)

        # Marquage des segments réutilisables (mêmes coordonnées que segment de base)
        base_segments = tollways_data.get('segments', [])
        for seg in optimized_segments:
            for idx, base_seg in enumerate(base_segments):
                # On suppose que les segments ont 'start' et 'end' (coordonnées [lon, lat] ou [lat, lon])
                seg_start = seg.get('start') or seg.get('start_coord')
                seg_end = seg.get('end') or seg.get('end_coord')
                base_start = base_seg.get('start_coord') if 'start_coord' in base_seg else None
                base_end = base_seg.get('end_coord') if 'end_coord' in base_seg else None
                # Si les coordonnées sont identiques (tolérance stricte)
                if seg_start == base_start and seg_end == base_end:
                    seg['reuse_base_segment'] = True
                    seg['base_segment_index'] = idx
                    break
                else:
                    seg['reuse_base_segment'] = False

        # Appliquer la logique des segments gratuits optimisée
        final_segments = self._apply_free_segments_logic(optimized_segments, selected_tolls)

        print(f"✅ {len(final_segments)} segments optimisés créés")
        return final_segments
    
    def _identify_segments_to_avoid(self, analysis: Dict, selected_tolls: List[MatchedToll]) -> List[int]:
        """
        Identifie les segments tollways à éviter selon la logique optimisée.
        
        LOGIQUE : 
        1. Éviter les segments qui contiennent des péages non-sélectionnés
        2. Éviter les "faux segments gratuits" dans les systèmes fermés
        
        Args:
            analysis: Analyse des segments vs péages
            selected_tolls: Péages sélectionnés à garder
            
        Returns:
            List[int]: Indices des segments à éviter
        """
        selected_toll_ids = {toll.osm_id for toll in selected_tolls}
        segments_to_avoid = []
        
        # Étape 1 : Segments avec péages non-sélectionnés
        for segment_info in analysis['segments_with_tolls']:
            segment_toll_ids = {toll.osm_id for toll in segment_info['tolls']}
            
            # Si le segment contient des péages non-sélectionnés, l'éviter
            if not segment_toll_ids.issubset(selected_toll_ids):
                segments_to_avoid.append(segment_info['segment_index'])
                toll_names = [toll.effective_name for toll in segment_info['tolls']]
                print(f"   🚫 Segment {segment_info['segment_index']} à éviter (péages non-sélectionnés: {toll_names})")
        
        # Étape 2 : Identifier les "faux segments gratuits" dans les systèmes fermés
        false_free_segments = self._identify_false_free_segments(analysis, selected_tolls)
        segments_to_avoid.extend(false_free_segments)
        
        return segments_to_avoid
    
    def _identify_false_free_segments(self, analysis: Dict, selected_tolls: List[MatchedToll]) -> List[int]:
        """
        Identifie les "faux segments gratuits" qui sont en réalité dans un système fermé.
        
        Un segment gratuit est "faux" s'il est entre deux péages fermés du même système,
        car on ne peut pas sortir de l'autoroute sans payer.
        
        Args:
            analysis: Analyse des segments vs péages
            selected_tolls: Péages sélectionnés
            
        Returns:
            List[int]: Indices des faux segments gratuits à éviter
        """
        false_free_segments = []
        
        # Obtenir les péages fermés non-sélectionnés
        all_tolls_on_route = []
        for segment_info in analysis['segments_with_tolls']:
            all_tolls_on_route.extend(segment_info['tolls'])
        
        unselected_closed_tolls = [
            toll for toll in all_tolls_on_route 
            if toll.csv_role == 'F' and toll not in selected_tolls
        ]
        
        if len(unselected_closed_tolls) < 2:
            return false_free_segments
        
        print(f"   🔍 Analyse des faux segments gratuits entre {len(unselected_closed_tolls)} péages fermés non-sélectionnés...")
        
        # Pour chaque segment gratuit, vérifier s'il est entre deux péages fermés
        for free_segment_info in analysis['free_segments']:
            segment_index = free_segment_info['segment_index']
            
            # Trouver les péages fermés avant et après ce segment
            toll_before = self._find_nearest_closed_toll_before(segment_index, unselected_closed_tolls, analysis)
            toll_after = self._find_nearest_closed_toll_after(segment_index, unselected_closed_tolls, analysis)
            
            if toll_before and toll_after:
                # Vérifier s'ils sont du même système autoroutier (même préfixe)
                if self._are_tolls_same_system(toll_before, toll_after):
                    false_free_segments.append(segment_index)
                    print(f"   🚫 Segment gratuit {segment_index} identifié comme faux (entre {toll_before.effective_name} et {toll_after.effective_name})")
        
        return false_free_segments
    
    def _find_nearest_closed_toll_before(self, segment_index: int, closed_tolls: List[MatchedToll], analysis: Dict) -> Optional[MatchedToll]:
        """Trouve le péage fermé le plus proche avant un segment donné."""
        for i in range(segment_index - 1, -1, -1):
            for segment_info in analysis['segments_with_tolls']:
                if segment_info['segment_index'] == i:
                    for toll in segment_info['tolls']:
                        if toll in closed_tolls:
                            return toll
        return None
    
    def _find_nearest_closed_toll_after(self, segment_index: int, closed_tolls: List[MatchedToll], analysis: Dict) -> Optional[MatchedToll]:
        """Trouve le péage fermé le plus proche après un segment donné."""
        max_segments = max(info['segment_index'] for info in analysis['segments_with_tolls'] + analysis['free_segments'])
        
        for i in range(segment_index + 1, max_segments + 1):
            for segment_info in analysis['segments_with_tolls']:
                if segment_info['segment_index'] == i:
                    for toll in segment_info['tolls']:
                        if toll in closed_tolls:
                            return toll
        return None
    
    def _are_tolls_same_system(self, toll1: MatchedToll, toll2: MatchedToll) -> bool:
        """
        Vérifie si deux péages appartiennent au même système autoroutier.
        
        Utilise le préfixe des identifiants CSV (ex: APRR_F123 et APRR_F456 = même système APRR).
        """
        if not toll1.csv_id or not toll2.csv_id:
            return False
        
        # Extraire le préfixe (ex: "APRR" de "APRR_F123")
        prefix1 = toll1.csv_id.split('_')[0] if '_' in toll1.csv_id else toll1.csv_id
        prefix2 = toll2.csv_id.split('_')[0] if '_' in toll2.csv_id else toll2.csv_id
        
        return prefix1 == prefix2
    
    def _apply_free_segments_logic(
        self, 
        segments: List[Dict], 
        selected_tolls: List[MatchedToll]
    ) -> List[Dict]:
        """
        Applique la logique optimisée des segments gratuits.
        
        RÈGLE OPTIMISÉE : Ne pas utiliser les segments gratuits entre deux péages fermés.
        
        Args:
            segments: Segments calculés
            selected_tolls: Péages sélectionnés
            
        Returns:
            List[Dict]: Segments avec logique gratuits appliquée
        """
        print("🆓 Application logique segments gratuits optimisée...")
        
        # Identifier les péages fermés sélectionnés
        closed_tolls = [t for t in selected_tolls if t.csv_role == 'F']
        
        if len(closed_tolls) < 2:
            print("   ✅ Moins de 2 péages fermés, segments gratuits autorisés")
            return segments
        
        # Analyser les segments entre péages fermés
        optimized_segments = []
        
        for segment in segments:
            # Vérifier si c'est un segment gratuit entre deux péages fermés
            if self._is_free_segment_between_closed_tolls(segment, closed_tolls):
                print(f"   🚫 Segment gratuit supprimé (entre péages fermés)")
                continue
            
            optimized_segments.append(segment)
        
        print(f"✅ {len(optimized_segments)} segments après logique gratuits")
        return optimized_segments
    
    def _is_free_segment_between_closed_tolls(self, segment: Dict, closed_tolls: List[MatchedToll]) -> bool:
        """
        Vérifie si un segment gratuit est entre deux péages fermés.
        
        Args:
            segment: Segment à vérifier
            closed_tolls: Liste des péages fermés
            
        Returns:
            bool: True si le segment est entre deux péages fermés
        """
        # Logique simplifiée : vérifier si le segment est marqué comme gratuit
        # et s'il y a des péages fermés avant et après
        
        if segment.get('segment_type') != 'free':
            return False
        
        # Cette logique pourrait être affinée selon la structure exacte des segments
        # Pour l'instant, on considère que s'il y a plus de 2 péages fermés,
        # les segments gratuits intermédiaires doivent être évités
        
        return len(closed_tolls) >= 2
    
    def _calculate_segments_routes(self, segments: List[Dict], base_route_response: Dict = None, tollways_data: Dict = None) -> List[Dict]:
        """
        Calcule les routes pour chaque segment optimisé.
        Si un segment est marqué 'reuse_base_segment', on réutilise la portion de la route de base.
        
        Args:
            segments: Segments à calculer
            base_route_response: Réponse ORS de la route de base (pour réutilisation)
            tollways_data: Données des segments tollways (pour indexation)
        
        Returns:
            List[Dict]: Segments avec routes calculées
        """
        print("🛣️ Calcul des routes par segment...")
        calculated_segments = []
        base_coords = None
        if base_route_response:
            base_coords = RouteUtils.extract_route_coordinates(base_route_response)
        base_segments = tollways_data.get('segments', []) if tollways_data else []

        for i, segment in enumerate(segments):
            print(f"   Segment {i+1}/{len(segments)}...")
            if segment.get('reuse_base_segment') and base_coords and base_segments:
                idx = segment.get('base_segment_index')
                if idx is not None and idx < len(base_segments):
                    base_seg = base_segments[idx]
                    start_idx = base_seg.get('start_waypoint')
                    end_idx = base_seg.get('end_waypoint')
                    # Extraire portion de la route de base
                    segment_coords = base_coords[start_idx:end_idx+1]
                    route_result = {
                        'geometry': segment_coords,
                        'start': segment.get('start'),
                        'end': segment.get('end'),
                        'segment_type': segment.get('segment_type'),
                        'description': segment.get('description', 'Segment réutilisé'),
                        'reused': True
                    }
                    calculated_segments.append(route_result)
                    print(f"   ♻️ Segment {i+1} réutilisé depuis la route de base")
                    continue
            # Sinon, calcul classique
            adapted_segment = self._adapt_segment_format(segment)
            route_result = self.route_calculator.calculate_segment_route(adapted_segment)
            if route_result:
                calculated_segments.append(route_result)
                print(f"   ✅ Segment {i+1} calculé")
            else:
                print(f"   ❌ Échec segment {i+1}")
                return None  # Échec global si un segment échoue
        print(f"✅ {len(calculated_segments)} segments calculés")
        return calculated_segments
    
    def _optimize_final_assembly(self, segments: List[Dict]) -> List[Dict]:
        """
        Optimise l'assemblage final des segments pour éviter les redondances.
        
        Args:
            segments: Segments bruts créés
            
        Returns:
            List[Dict]: Segments optimisés et assemblés
        """
        if not segments:
            return []
        
        print(f"🔧 Optimisation assemblage final ({len(segments)} segments bruts)...")
        
        # Regrouper les segments consécutifs d'évitement
        optimized = []
        i = 0
        last_end = None
        while i < len(segments):
            current_segment = segments[i]
            # Vérification de la continuité des coordonnées
            current_start = current_segment.get('start') or current_segment.get('start_coord')
            if last_end is not None and current_start != last_end:
                print(f"   ⚠️ Segment {i} ignoré : début {current_start} ne correspond pas à la fin précédente {last_end}")
                i += 1
                continue
            if current_segment.get('segment_type') == 'avoid_tolls':
                # Regrouper tous les segments d'évitement consécutifs
                avoidance_group = [current_segment]
                j = i + 1
                while j < len(segments) and segments[j].get('segment_type') == 'avoid_tolls':
                    avoidance_group.append(segments[j])
                    j += 1
                if len(avoidance_group) > 1:
                    merged_segment = self._merge_avoidance_segments(avoidance_group)
                    optimized.append(merged_segment)
                    print(f"   🔗 {len(avoidance_group)} segments d'évitement fusionnés")
                    last_end = merged_segment.get('end') or merged_segment.get('end_coord')
                else:
                    optimized.append(current_segment)
                    last_end = current_segment.get('end') or current_segment.get('end_coord')
                i = j
            else:
                optimized.append(current_segment)
                last_end = current_segment.get('end') or current_segment.get('end_coord')
                i += 1
        print(f"   ✅ {len(optimized)} segments après optimisation")
        return optimized
    
    def _merge_avoidance_segments(self, avoidance_segments: List[Dict]) -> Dict:
        """
        Fusionne plusieurs segments d'évitement consécutifs en un seul.
        
        Args:
            avoidance_segments: Segments d'évitement à fusionner
            
        Returns:
            Dict: Segment d'évitement fusionné
        """
        if len(avoidance_segments) == 1:
            return avoidance_segments[0]
        
        first = avoidance_segments[0]
        last = avoidance_segments[-1]
        
        # Calculer une nouvelle route d'évitement globale
        try:
            global_route = self.ors.get_route_avoid_tollways(
                [first['start_coord'], last['end_coord']]
            )
            
            if global_route:
                return {
                    'segment_type': 'avoid_tolls',
                    'strategy': 'merged_avoidance',
                    'start': first['start_coord'],
                    'end': last['end_coord'],
                    'start_coord': first['start_coord'],
                    'end_coord': last['end_coord'],
                    'route': global_route,
                    'merged_count': len(avoidance_segments),
                    'description': f"Évitement fusionné de {len(avoidance_segments)} segments"
                }
        except Exception as e:
            print(f"   ⚠️ Erreur fusion segments : {e}")
        
        # Fallback : retourner le premier segment
        return first
    
    def _calculate_distance(self, point1: List[float], point2: List[float]) -> float:
        """
        Calcule la distance entre deux points en km.
        
        Args:
            point1: [lon, lat]
            point2: [lon, lat]
            
        Returns:
            float: Distance en kilomètres
        """
        import math
        
        lon1, lat1 = math.radians(point1[0]), math.radians(point1[1])
        lon2, lat2 = math.radians(point2[0]), math.radians(point2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return 6371 * c  # Rayon de la Terre en km
    
    def _calculate_distance_meters(self, coord1: List[float], coord2: List[float]) -> float:
        """
        Calcule la distance entre deux points en mètres.
        
        Args:
            coord1: Premier point [lat, lon]
            coord2: Deuxième point [lat, lon]
            
        Returns:
            float: Distance en mètres
        """
        import math
        
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return 6371000.0 * c  # Rayon de la Terre en mètres
    
    def _adapt_segment_format(self, segment: Dict) -> Dict:
        """
        Adapte le format d'un segment pour le SegmentRouteCalculator.
        
        Args:
            segment: Segment original
            
        Returns:
            Dict: Segment adapté avec les clés attendues
        """
        # Si le segment a déjà le bon format, le retourner tel quel
        if all(key in segment for key in ['start', 'end', 'segment_type', 'description']):
            return segment
        
        # Sinon, essayer d'adapter le format
        adapted = {
            'start': segment.get('start_coord', segment.get('start', [0, 0])),
            'end': segment.get('end_coord', segment.get('end', [0, 0])),
            'segment_type': segment.get('segment_type', segment.get('type', 'normal')),
            'description': segment.get('description', f"Segment {segment.get('segment_type', 'normal')} {segment.get('id', 'inconnu')}")
        }
        
        print(f"   🔧 Segment adapté : {adapted['description']}")
        return adapted
