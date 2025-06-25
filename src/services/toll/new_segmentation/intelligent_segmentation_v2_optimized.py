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
        self.toll_deduplicator = TollDeduplicator()
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
            base_route, tollways_data = self._get_base_route_with_tollways(coordinates)
            if not base_route:
                return None
            
            # Étape 2 : Identifier péages pré-matchés SUR les segments
            route_coords = RouteUtils.extract_route_coordinates(base_route)
            tolls_on_segments = self._identify_prematched_tolls_on_segments(
                tollways_data['segments'], route_coords
            )
            
            # CAS SPÉCIAUX : optimisations directes
            if len(tolls_on_segments) < target_tolls:
                print(f"⚠️ Pas assez de péages ({len(tolls_on_segments)} < {target_tolls})")
                return self.special_cases.format_base_route_as_result(base_route)
            
            if len(tolls_on_segments) == target_tolls:
                print(f"✅ Nombre exact de péages trouvé")
                return self.special_cases.format_base_route_as_result(base_route)
            
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
                return self.special_cases.format_base_route_as_result(base_route)
            
            # Étape 5 : Calcul des routes pour chaque segment
            print("🛣️ Étape 5 : Calcul des routes par segment...")
            calculated_segments = self._calculate_segments_routes(segments)
            
            if not calculated_segments:
                print("❌ Échec calcul des segments")
                return self.special_cases.format_base_route_as_result(base_route)
            
            # Étape 6 : Assemblage final optimisé
            print("🔧 Étape 6 : Assemblage final optimisé...")
            final_route = self._assemble_optimized_route(calculated_segments)
            
            if not final_route:
                print("❌ Échec assemblage final")
                return self.special_cases.format_base_route_as_result(base_route)
            
            print("✅ Segmentation V2 Optimisée réussie")
            return final_route
    
    def _get_base_route_with_tollways(self, coordinates: List[List[float]]) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Obtient la route de base avec les segments tollways.
        
        Returns:
            Tuple[route, tollways_data]: Route de base et données tollways
        """
        print("🛣️ Étape 1 : Route de base + segments tollways...")
        
        # Route de base sans évitement
        response = self.ors.get_base_route(coordinates)
        if not response or response.get('status') != 'success':
            print("❌ Échec obtention route de base")
            return None, None
        
        base_route = response.get('data', {}).get('routes', [{}])[0]
        if not base_route:
            print("❌ Route de base vide")
            return None, None
        
        # Extraire segments tollways
        tollways_data = self._extract_tollways_segments(base_route)
        if not tollways_data:
            print("⚠️ Aucun segment tollway trouvé")
            return base_route, {'segments': []}
        
        print(f"✅ Route de base obtenue avec {len(tollways_data['segments'])} segments tollways")
        return base_route, tollways_data
    
    def _extract_tollways_segments(self, route: Dict) -> Optional[Dict]:
        """
        Extrait les segments tollways de la route ORS.
        
        Args:
            route: Route ORS complète
            
        Returns:
            Dict contenant les segments tollways analysés
        """
        geometry = route.get('geometry')
        if not geometry:
            return None
        
        # Chercher les segments dans les extras
        extras = route.get('extras', {})
        tollways_info = extras.get('tollways', {})
        
        if not tollways_info:
            return None
        
        segments = []
        values = tollways_info.get('values', [])
        
        for segment_info in values:
            # Format ORS : [start_index, end_index, is_toll_flag]
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
        
        # Filtrer les péages qui sont sur les segments tollways
        tolls_on_segments = []
        
        for segment in segments:
            if not segment['is_toll']:
                continue  # Ignorer les segments gratuits
            
            # Extraire les coordonnées du segment
            start_idx = segment['start_waypoint']
            end_idx = segment['end_waypoint']
            
            if end_idx >= len(route_coords):
                continue
            
            segment_coords = route_coords[start_idx:end_idx + 1]
            
            # Trouver les péages pré-matchés sur ce segment
            segment_tolls = self._find_prematched_tolls_on_segment(
                prematched_tolls, segment_coords
            )
            
            tolls_on_segments.extend(segment_tolls)
        
        # Déduplication
        tolls_on_segments = self.toll_deduplicator.deduplicate_tolls(tolls_on_segments)
        
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
        Sélectionne les péages cibles en priorisant le système ouvert.
        
        OPTIMISATION : Utilise directement le csv_role pré-calculé.
        
        Args:
            tolls_on_segments: Péages disponibles sur les segments
            target_count: Nombre de péages souhaités
            
        Returns:
            List[MatchedToll]: Péages sélectionnés
        """
        print(f"🎯 Étape 3 : Sélection {target_count} péages cibles (prioriser système ouvert)...")
        
        if len(tolls_on_segments) <= target_count:
            return tolls_on_segments
        
        # Séparer par type de système (ouvert/fermé)
        open_system_tolls = [t for t in tolls_on_segments if t.csv_role == 'O']
        closed_system_tolls = [t for t in tolls_on_segments if t.csv_role != 'O']
        
        print(f"   🔓 Système ouvert : {len(open_system_tolls)} péages")
        print(f"   🔒 Système fermé : {len(closed_system_tolls)} péages")
        
        selected = []
        
        # Prioriser les péages à système ouvert
        selected.extend(open_system_tolls[:target_count])
        
        # Compléter avec les péages fermés si nécessaire
        remaining = target_count - len(selected)
        if remaining > 0:
            selected.extend(closed_system_tolls[:remaining])
        
        print(f"✅ {len(selected)} péages sélectionnés")
        return selected
    
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
        
        # Analyser les segments tollways vs péages sélectionnés
        analysis = self.tollways_analyzer.analyze_segments_for_tolls(
            tollways_data['segments'], selected_tolls, route_coords
        )
        
        # Identifier les segments à éviter
        segments_to_avoid = self._identify_segments_to_avoid(analysis, selected_tolls)
        
        # Créer les segments d'évitement avec logique optimisée
        optimized_segments = self.avoidance_manager.create_avoidance_segments(
            tollways_data['segments'],
            segments_to_avoid,
            route_coords,
            coordinates[0],
            coordinates[1]
        )
        
        # Appliquer la logique des segments gratuits optimisée
        final_segments = self._apply_free_segments_logic(optimized_segments, selected_tolls)
        
        print(f"✅ {len(final_segments)} segments optimisés créés")
        return final_segments
    
    def _identify_segments_to_avoid(self, analysis: Dict, selected_tolls: List[MatchedToll]) -> List[int]:
        """
        Identifie les segments tollways à éviter selon la logique optimisée.
        
        LOGIQUE : Éviter les segments qui contiennent des péages non-sélectionnés.
        
        Args:
            analysis: Analyse des segments vs péages
            selected_tolls: Péages sélectionnés à garder
            
        Returns:
            List[int]: Indices des segments à éviter
        """
        selected_toll_ids = {toll.osm_id for toll in selected_tolls}
        segments_to_avoid = []
        
        for segment_info in analysis['segments_with_tolls']:
            segment_toll_ids = {toll.osm_id for toll in segment_info['tolls']}
            
            # Si le segment contient des péages non-sélectionnés, l'éviter
            if not segment_toll_ids.issubset(selected_toll_ids):
                segments_to_avoid.append(segment_info['segment_index'])
                print(f"   🚫 Segment {segment_info['segment_index']} à éviter (péages non-sélectionnés)")
        
        return segments_to_avoid
    
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
    
    def _calculate_segments_routes(self, segments: List[Dict]) -> List[Dict]:
        """
        Calcule les routes pour chaque segment optimisé.
        
        Args:
            segments: Segments à calculer
            
        Returns:
            List[Dict]: Segments avec routes calculées
        """
        print("🛣️ Calcul des routes par segment...")
        
        calculated_segments = []
        
        for i, segment in enumerate(segments):
            print(f"   Segment {i+1}/{len(segments)}...")
            
            # Calculer la route pour ce segment
            route_result = self.route_calculator.calculate_segment_route(segment)
            
            if route_result:
                calculated_segments.append(route_result)
                print(f"   ✅ Segment {i+1} calculé")
            else:
                print(f"   ❌ Échec segment {i+1}")
                return None  # Échec global si un segment échoue
        
        print(f"✅ {len(calculated_segments)} segments calculés")
        return calculated_segments
    
    def _assemble_optimized_route(self, calculated_segments: List[Dict]) -> Optional[Dict]:
        """
        Assemble la route finale à partir des segments calculés.
        
        Args:
            calculated_segments: Segments avec routes calculées
            
        Returns:
            Dict: Route finale assemblée
        """
        print("🔧 Assemblage final optimisé...")
        
        # Utiliser l'assembleur existant
        final_route = self.route_assembler.assemble_segments(calculated_segments)
        
        if final_route:
            print("✅ Assemblage réussi")
            return final_route
        else:
            print("❌ Échec assemblage")
            return None
    
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
