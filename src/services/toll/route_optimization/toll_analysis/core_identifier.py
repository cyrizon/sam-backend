"""
Core Toll Identification
=======================

Module principal pour l'identification des péages avec le nouveau système unifié.
Responsabilité : Orchestration des phases d'identification.
"""

from typing import List, Dict, Optional
import math
from .spatial.unified_spatial_manager import UnifiedSpatialIndexManager
from .detection.distance_calculator import OptimizedDistanceCalculator
from .detection.toll_classifier import TollClassifier


class CoreTollIdentifier:
    """Identifieur de péages optimisé avec cache V2."""
    
    def __init__(self):
        """Initialise l'identifieur avec les nouveaux index unifiés."""
        self.spatial_manager = UnifiedSpatialIndexManager()
        self.classifier = TollClassifier()
        print("🔍 Core Toll Identifier initialisé avec cache V2")
    
    def identify_tolls_on_route(
        self, 
        route_coordinates: List[List[float]], 
        tollway_segments: List[Dict] = None
    ) -> Dict:
        """
        Identifie les péages sur une route donnée.
        
        Args:
            route_coordinates: Coordonnées de la route
            tollway_segments: Segments tollways (optionnel)
            
        Returns:
            Résultat d'identification avec péages détectés
        """
        print("🔍 Identification des péages sur la route...")
        
        if not self._validate_input(route_coordinates):
            return self._create_empty_result()
        
        try:
            # Phase 1: Recherche spatiale des péages proches
            nearby_tolls = self._find_nearby_tolls(route_coordinates)
            if not nearby_tolls:
                return self._create_empty_result()
            
            # Phase 2: Calcul des distances précises
            toll_distances = self._calculate_precise_distances(nearby_tolls, route_coordinates)
            
            # Phase 3: Classification et filtrage
            classified_tolls = self._classify_tolls(toll_distances)
            
            # Phase 3.5: Déduplication des péages
            deduplicated_tolls = self._deduplicate_tolls(classified_tolls)
            
            # Phase 3.7: Tri des péages par position sur la route
            sorted_tolls = self._sort_tolls_by_route_position(deduplicated_tolls, route_coordinates)
            
            # Phase 4: Construction du résultat final
            return self._build_identification_result(sorted_tolls, route_coordinates)
            
        except Exception as e:
            print(f"❌ Erreur identification péages : {e}")
            return self._create_empty_result()
    
    def _validate_input(self, route_coordinates: List[List[float]]) -> bool:
        """Valide les données d'entrée."""
        if not route_coordinates or len(route_coordinates) < 2:
            print("❌ Coordonnées de route invalides")
            return False
        return True
    
    def _find_nearby_tolls(self, route_coordinates: List[List[float]]) -> List:
        """Phase 1: Trouve les péages proches de la route."""
        print("   🗂️ Phase 1: Recherche spatiale des péages...")
        
        nearby_tolls = self.spatial_manager.get_nearby_tolls(route_coordinates)
        
        if not nearby_tolls:
            print("   ⚠️ Aucun péage trouvé dans la zone")
            return []
        
        print(f"   ✅ {len(nearby_tolls)} péages trouvés dans la zone")
        return nearby_tolls
    
    def _calculate_precise_distances(self, tolls: List, route_coordinates: List[List[float]]) -> List[Dict]:
        """Phase 2: Calcule les distances précises pour chaque péage."""
        print("   📏 Phase 2: Calcul des distances précises...")
        
        toll_distances = []
        
        for toll in tolls:
            try:
                # Utiliser les nouvelles propriétés de TollBoothStation
                toll_coords = toll.get_coordinates()
                
                # Calculer la distance minimale à la route
                min_distance, _, _ = OptimizedDistanceCalculator.optimized_point_to_polyline_meters(
                    toll_coords, route_coordinates
                )
                
                toll_distances.append({
                    'toll': toll,
                    'coordinates': toll_coords,
                    'min_distance_m': min_distance,
                    'is_on_route': min_distance <= 50,  # 50m de tolérance
                    'toll_type': 'ouvert' if toll.is_open_toll else 'fermé',
                    'operator': toll.operator or 'Inconnu'
                })
                
            except Exception as e:
                print(f"   ⚠️ Erreur calcul distance pour péage {toll.osm_id}: {e}")
                continue
        
        print(f"   ✅ Distances calculées pour {len(toll_distances)} péages")
        return toll_distances
    
    def _classify_tolls(self, toll_distances: List[Dict]) -> Dict:
        """Phase 3: Classifie les péages selon leur position."""
        print("   🏷️ Phase 3: Classification des péages...")
        
        on_route = []
        nearby = []
        
        for toll_data in toll_distances:
            if toll_data['is_on_route']:
                on_route.append(toll_data)
            elif toll_data['min_distance_m'] <= 1000:  # 1km autour
                nearby.append(toll_data)
        
        # Trier par distance
        on_route.sort(key=lambda x: x['min_distance_m'])
        nearby.sort(key=lambda x: x['min_distance_m'])
        
        print(f"   ✅ Classification : {len(on_route)} sur route, {len(nearby)} à proximité")
        
        return {
            'on_route': on_route,
            'nearby': nearby,
            'all_processed': toll_distances
        }
    
    def _build_identification_result(self, classified_tolls: Dict, route_coordinates: List[List[float]]) -> Dict:
        """Phase 4: Construit le résultat final d'identification."""
        print("   📋 Phase 4: Construction du résultat...")
        
        tolls_on_route = classified_tolls['on_route']
        nearby_tolls = classified_tolls['nearby']
        
        # Statistiques par type
        open_tolls_count = sum(1 for t in tolls_on_route if t['toll_type'] == 'ouvert')
        closed_tolls_count = sum(1 for t in tolls_on_route if t['toll_type'] == 'fermé')
        
        # Opérateurs présents
        operators = list(set(t['operator'] for t in tolls_on_route if t['operator'] != 'Inconnu'))
        
        # Statistiques de déduplication
        duplicates_removed = classified_tolls.get('duplicates_removed', 0)
        
        result = {
            'identification_success': True,
            'total_tolls_on_route': len(tolls_on_route),
            'tolls_on_route': tolls_on_route,
            'nearby_tolls': nearby_tolls,
            'statistics': {
                'open_tolls': open_tolls_count,
                'closed_tolls': closed_tolls_count,
                'operators': operators,
                'total_nearby': len(nearby_tolls),
                'duplicates_removed': duplicates_removed
            },
            'route_info': {
                'total_points': len(route_coordinates),
                'start_point': route_coordinates[0],
                'end_point': route_coordinates[-1]
            }
        }
        
        if duplicates_removed > 0:
            print(f"   ✅ Identification terminée : {result['total_tolls_on_route']} péages sur route ({duplicates_removed} doublons supprimés)")
        else:
            print(f"   ✅ Identification terminée : {result['total_tolls_on_route']} péages sur route")
        return result
    
    def _create_empty_result(self) -> Dict:
        """Crée un résultat vide en cas d'échec."""
        return {
            'identification_success': False,
            'total_tolls_on_route': 0,
            'tolls_on_route': [],
            'nearby_tolls': [],
            'statistics': {
                'open_tolls': 0,
                'closed_tolls': 0,
                'operators': [],
                'total_nearby': 0
            },
            'route_info': {}
        }
    
    def get_spatial_index_stats(self) -> Dict:
        """Retourne les statistiques des index spatiaux."""
        return self.spatial_manager.get_unified_stats()
    
    def _deduplicate_tolls(self, classified_tolls: Dict) -> Dict:
        """Phase 3.5: Déduplique les péages basé sur la proximité (<1m) et similarité sémantique."""
        print("   🔄 Phase 3.5: Déduplication des péages...")
        
        # Debug: afficher les péages AVANT déduplication
        print(f"   🔍 Péages AVANT déduplication: {len(classified_tolls['on_route'])}")
        for i, toll_data in enumerate(classified_tolls['on_route']):
            toll_station = toll_data.get('toll')
            toll_name = toll_station.display_name if toll_station and hasattr(toll_station, 'display_name') else "Inconnu"
            print(f"     {i+1}. {toll_name}")
        
        # Dédupliquer SEULEMENT les péages sur la route
        deduplicated_on_route = self._deduplicate_toll_list(classified_tolls['on_route'])
        
        # Debug: afficher les péages APRÈS déduplication  
        print(f"   🔍 Péages APRÈS déduplication: {len(deduplicated_on_route)}")
        for i, toll_data in enumerate(deduplicated_on_route):
            toll_station = toll_data.get('toll')
            toll_name = toll_station.display_name if toll_station and hasattr(toll_station, 'display_name') else "Inconnu"
            print(f"     {i+1}. {toll_name}")
        
        # NE PAS dédupliquer les péages à proximité - on s'en fout
        deduplicated_nearby = classified_tolls['nearby']
        
        # Compter les doublons supprimés (uniquement ceux sur la route)
        original_count = len(classified_tolls['on_route'])
        new_count = len(deduplicated_on_route)
        duplicates_removed = original_count - new_count
        
        if duplicates_removed > 0:
            print(f"   ✅ Déduplication : {duplicates_removed} doublons supprimés")
        else:
            print("   ✅ Déduplication : aucun doublon détecté")
        
        return {
            'on_route': deduplicated_on_route,
            'nearby': deduplicated_nearby,
            'all_processed': classified_tolls['all_processed'],
            'duplicates_removed': duplicates_removed
        }
    
    def _deduplicate_toll_list(self, toll_list: List[Dict]) -> List[Dict]:
        """Déduplique une liste de péages basé sur la proximité et similarité."""
        if len(toll_list) <= 1:
            return toll_list
        
        deduplicated = []
        processed_indices = set()
        
        for i, toll_data in enumerate(toll_list):
            if i in processed_indices:
                continue
            
            # Chercher les doublons de ce péage
            duplicates = [i]
            
            for j in range(i + 1, len(toll_list)):
                if j in processed_indices:
                    continue
                
                if self._are_tolls_duplicates(toll_data, toll_list[j]):
                    duplicates.append(j)
                    processed_indices.add(j)
            
            # Garder le meilleur candidat parmi les doublons
            best_toll = self._select_best_toll_candidate(
                [toll_list[idx] for idx in duplicates]
            )
            
            deduplicated.append(best_toll)
            processed_indices.add(i)
        
        return deduplicated
    
    def _are_tolls_duplicates(self, toll1_data: Dict, toll2_data: Dict) -> bool:
        """Détermine si deux péages sont des doublons."""
        toll1 = toll1_data['toll']
        toll2 = toll2_data['toll']
        coords1 = toll1_data['coordinates']
        coords2 = toll2_data['coordinates']
        
        # Calcul de distance entre les deux péages
        distance = self._calculate_distance_between_points(coords1, coords2)
        
        # Si distance > 1m, pas des doublons
        if distance > 1.0:
            return False
        
        # Vérifier la similarité sémantique
        return self._are_semantically_similar(toll1, toll2)
    
    def _calculate_distance_between_points(self, coords1: List[float], coords2: List[float]) -> float:
        """Calcule la distance en mètres entre deux points (lat, lon)."""
        lat1, lon1 = coords1[1], coords1[0]  # coords sont [lon, lat]
        lat2, lon2 = coords2[1], coords2[0]
        
        # Formule haversine pour distance précise
        R = 6371000  # Rayon de la Terre en mètres
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return distance
    
    def _are_semantically_similar(self, toll1, toll2) -> bool:
        """Vérifie si deux péages sont sémantiquement similaires."""
        # Même opérateur ou opérateurs inconnus
        op1 = getattr(toll1, 'operator', None) or 'Inconnu'
        op2 = getattr(toll2, 'operator', None) or 'Inconnu'
        
        # Si les deux ont des opérateurs connus et différents, pas similaires
        if op1 != 'Inconnu' and op2 != 'Inconnu' and op1 != op2:
            return False
        
        # Même autoroute si disponible
        autoroute1 = getattr(toll1, 'autoroute', None) or ''
        autoroute2 = getattr(toll2, 'autoroute', None) or ''
        
        if autoroute1 and autoroute2 and autoroute1 != autoroute2:
            return False
        
        # Même type de péage
        type1 = 'ouvert' if getattr(toll1, 'is_open_toll', False) else 'fermé'
        type2 = 'ouvert' if getattr(toll2, 'is_open_toll', False) else 'fermé'
        
        if type1 != type2:
            return False
        
        # Noms similaires si disponibles
        name1 = getattr(toll1, 'nom', '').lower()
        name2 = getattr(toll2, 'nom', '').lower()
        
        if name1 and name2 and name1 != name2:
            # Vérifier si l'un est contenu dans l'autre
            if name1 not in name2 and name2 not in name1:
                return False
        
        return True
    
    def _select_best_toll_candidate(self, candidates: List[Dict]) -> Dict:
        """Sélectionne le meilleur candidat parmi les doublons."""
        if len(candidates) == 1:
            return candidates[0]
        
        # Critères de priorité :
        # 1. Distance minimale à la route
        # 2. Présence d'informations complètes (nom, opérateur)
        # 3. ID OSM le plus bas (cohérence)
        
        best = candidates[0]
        
        for candidate in candidates[1:]:
            # Priorité 1: Distance plus faible
            if candidate['min_distance_m'] < best['min_distance_m']:
                best = candidate
                continue
            elif candidate['min_distance_m'] > best['min_distance_m']:
                continue
            
            # Priorité 2: Informations plus complètes
            best_info_score = self._calculate_info_completeness_score(best['toll'])
            candidate_info_score = self._calculate_info_completeness_score(candidate['toll'])
            
            if candidate_info_score > best_info_score:
                best = candidate
                continue
            elif candidate_info_score < best_info_score:
                continue
            
            # Priorité 3: ID OSM le plus bas
            best_osm_id = getattr(best['toll'], 'osm_id', float('inf'))
            candidate_osm_id = getattr(candidate['toll'], 'osm_id', float('inf'))
            
            if candidate_osm_id < best_osm_id:
                best = candidate
        
        return best
    
    def _calculate_info_completeness_score(self, toll) -> int:
        """Calcule un score de complétude des informations d'un péage."""
        score = 0
        
        if getattr(toll, 'nom', None):
            score += 2
        if getattr(toll, 'operator', None) and toll.operator != 'Inconnu':
            score += 2
        if getattr(toll, 'autoroute', None):
            score += 1
        if getattr(toll, 'osm_id', None):
            score += 1
        
        return score
    
    def _sort_tolls_by_route_position(self, classified_tolls: Dict, route_coordinates: List[List[float]]) -> Dict:
        """Phase 3.7: Trie les péages par leur position le long de la route."""
        print("   📍 Phase 3.7: Tri des péages par position sur la route...")
        
        # Trier les péages sur la route par position
        sorted_on_route = self._sort_toll_list_by_position(classified_tolls['on_route'], route_coordinates)
        
        # Les péages à proximité ne nécessitent pas de tri par position
        nearby_tolls = classified_tolls['nearby']
        
        print(f"   ✅ Tri terminé : {len(sorted_on_route)} péages sur route triés par position")
        
        return {
            'on_route': sorted_on_route,
            'nearby': nearby_tolls,
            'all_processed': classified_tolls['all_processed'],
            'duplicates_removed': classified_tolls.get('duplicates_removed', 0)
        }
    
    def _sort_toll_list_by_position(self, toll_list: List[Dict], route_coordinates: List[List[float]]) -> List[Dict]:
        """Trie une liste de péages par leur position le long de la route."""
        if len(toll_list) <= 1:
            return toll_list
        
        # Calculer la position de chaque péage le long de la route
        tolls_with_position = []
        
        for toll_data in toll_list:
            toll_coords = toll_data['coordinates']
            position = self._calculate_position_along_route(toll_coords, route_coordinates)
            
            toll_data_with_position = toll_data.copy()
            toll_data_with_position['route_position'] = position
            tolls_with_position.append(toll_data_with_position)
            
            # Debug: récupérer le nom du péage correctement
            toll_station = toll_data.get('toll')  # Récupérer l'objet TollBoothStation
            if toll_station and hasattr(toll_station, 'display_name'):
                toll_name = toll_station.display_name
            else:
                toll_name = f"Péage inconnu"
            
            print(f"   🔍 {toll_name}: position {position:.4f} at {toll_coords}")
        
        # Trier par position croissante le long de la route
        sorted_tolls = sorted(tolls_with_position, key=lambda x: x['route_position'])
        
        return sorted_tolls
    
    def _calculate_position_along_route(self, toll_coords: List[float], route_coordinates: List[List[float]]) -> float:
        """
        Calcule la position d'un péage le long de la route (0.0 = début, 1.0 = fin).
        
        Args:
            toll_coords: Coordonnées du péage [lon, lat]
            route_coordinates: Coordonnées de la route
            
        Returns:
            Position normalisée entre 0.0 et 1.0
        """
        if len(route_coordinates) < 2:
            return 0.0
        
        min_distance = float('inf')
        closest_segment_index = 0
        closest_position_in_segment = 0.0
        
        # Trouver le segment de route le plus proche du péage
        for i in range(len(route_coordinates) - 1):
            point_a = route_coordinates[i]
            point_b = route_coordinates[i + 1]
            
            # Calculer la distance du péage au segment [point_a, point_b]
            distance, position_in_segment = self._distance_point_to_segment(toll_coords, point_a, point_b)
            
            if distance < min_distance:
                min_distance = distance
                closest_segment_index = i
                closest_position_in_segment = position_in_segment
        
        # Calculer la position normalisée le long de toute la route
        # Position = (index_segment + position_dans_segment) / nombre_total_segments
        total_segments = len(route_coordinates) - 1
        if total_segments == 0:
            return 0.0
        
        route_position = (closest_segment_index + closest_position_in_segment) / total_segments
        return max(0.0, min(1.0, route_position))  # Borner entre 0 et 1
    
    def _distance_point_to_segment(self, point: List[float], seg_a: List[float], seg_b: List[float]) -> tuple:
        """
        Calcule la distance d'un point à un segment et la position relative sur le segment.
        
        Returns:
            Tuple (distance_en_metres, position_sur_segment_0_1)
        """
        # Convertir en coordonnées métriques approximatives
        px, py = point[0], point[1]
        ax, ay = seg_a[0], seg_a[1]
        bx, by = seg_b[0], seg_b[1]
        
        # Vecteur segment
        dx = bx - ax
        dy = by - ay
        
        # Longueur du segment au carré
        segment_length_sq = dx * dx + dy * dy
        
        if segment_length_sq == 0:
            # Segment de longueur nulle
            distance = math.sqrt((px - ax) ** 2 + (py - ay) ** 2)
            return distance * 111139, 0.0  # Conversion approximative en mètres
        
        # Projection du point sur la ligne du segment
        t = ((px - ax) * dx + (py - ay) * dy) / segment_length_sq
        t = max(0.0, min(1.0, t))  # Borner entre 0 et 1
        
        # Point le plus proche sur le segment
        closest_x = ax + t * dx
        closest_y = ay + t * dy
        
        # Distance au point le plus proche
        distance_deg = math.sqrt((px - closest_x) ** 2 + (py - closest_y) ** 2)
        distance_m = distance_deg * 111139  # Conversion approximative en mètres
        
        return distance_m, t
