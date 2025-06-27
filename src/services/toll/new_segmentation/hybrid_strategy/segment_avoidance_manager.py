"""
segment_avoidance_manager.py
---------------------------

Gestionnaire des stratégies d'évitement de segments payants.
Implémente les 3 niveaux d'évitement :
1. Fin → Fin (segments gratuits)
2. Début → Fin (segments gratuits élargi)
3. Sortie → Entrée (infrastructure autoroutière)

Responsabilité unique :
- Gérer l'évitement des segments payants avec les 3 stratégies
- Calculer les routes d'évitement
- Fallback progressif entre les stratégies
"""

from typing import List, Dict, Optional, Tuple
from src.cache.models.matched_toll import MatchedToll


class SegmentAvoidanceManager:
    """Gestionnaire des évitements de segments payants."""
    
    def __init__(self, ors_service, osm_parser):
        """
        Initialise le gestionnaire d'évitement.
        
        Args:
            ors_service: Service ORS pour les calculs de routes
            osm_parser: Parser OSM pour trouver sorties/entrées
        """
        self.ors = ors_service
        self.osm_parser = osm_parser
    
    def create_avoidance_segments(
        self, 
        tollways_segments: List[Dict], 
        segments_to_avoid: List[Dict],
        route_coords: List[List[float]],
        start_coord: List[float],
        end_coord: List[float]
    ) -> List[Dict]:
        """
        Crée les segments d'évitement pour les segments payants à éviter.
        
        Args:
            tollways_segments: Tous les segments tollways
            segments_to_avoid: Segments à éviter
            route_coords: Coordonnées de la route complète
            start_coord: Point de départ
            end_coord: Point d'arrivée
            
        Returns:
            List[Dict]: Segments d'évitement calculés
        """
        print("🛣️ Création des segments d'évitement...")
        print(f"   🔍 DEBUG: segments_to_avoid = {segments_to_avoid}")
        print(f"   🔍 DEBUG: type(segments_to_avoid) = {type(segments_to_avoid)}")
        print(f"   🔍 DEBUG: len(tollways_segments) = {len(tollways_segments)}")
        
        # Regrouper les segments consécutifs à éviter
        avoidance_groups = self._group_consecutive_segments_to_avoid(segments_to_avoid)
        print(f"   📊 {len(avoidance_groups)} groupe(s) d'évitement détecté(s)")
        
        avoidance_segments = []
        current_position = start_coord
        processed_segments = set()  # Pour éviter les doublons
        covered_indices = set()     # Pour éviter d'ajouter des segments normaux déjà couverts
        for group in avoidance_groups:
            covered_indices.update(range(group[0], group[-1]+1))
        
        for i, segment in enumerate(tollways_segments):
            if i in processed_segments:
                print(f"   ⏭️ Segment {i} déjà traité, ignoré")
                continue
            
            # Correction : ne pas ajouter de segment normal si déjà couvert par un évitement groupé
            if i not in segments_to_avoid and i in covered_indices:
                print(f"   ⏭️ Segment {i} normal déjà couvert par un évitement groupé, ignoré")
                processed_segments.add(i)
                continue
            
            print(f"   🔍 DEBUG: Segment {i}, à éviter ? {i in segments_to_avoid}")
            
            # Vérifier si ce segment est dans un groupe d'évitement
            avoidance_group = self._find_avoidance_group_for_segment(i, avoidance_groups)
            
            if avoidance_group and i == avoidance_group[0]:  # Premier segment du groupe
                # Créer un évitement groupé pour tous les segments consécutifs
                print(f"   🚫 Évitement groupé segments {avoidance_group[0]} à {avoidance_group[-1]}")
                
                avoidance_segment = self._create_grouped_avoidance_segment(
                    avoidance_group, tollways_segments, route_coords, segments_to_avoid
                )
                
                if avoidance_segment:
                    avoidance_segments.append(avoidance_segment)
                    current_position = avoidance_segment['end_coord']
                    print(f"      ✅ Évitement groupé créé avec succès")
                    # Marquer tous les segments du groupe comme traités
                    processed_segments.update(avoidance_group)
                else:
                    print(f"      ❌ Évitement groupé échoué, segments traités individuellement")
                    # Fallback : traiter individuellement
                    for seg_idx in avoidance_group:
                        segment_to_avoid = tollways_segments[seg_idx]
                        prev_free = self._find_previous_free_segment(tollways_segments, seg_idx, segments_to_avoid)
                        next_free = self._find_next_free_segment(tollways_segments, seg_idx, segments_to_avoid)
                        
                        single_avoidance = self._create_single_avoidance_segment(
                            segment_to_avoid, prev_free, next_free, route_coords
                        )
                        if single_avoidance:
                            avoidance_segments.append(single_avoidance)
                            current_position = single_avoidance['end_coord']
                        
                        # Marquer ce segment comme traité
                        processed_segments.add(seg_idx)
                
            elif avoidance_group:
                # Segment déjà traité dans le groupe, passer
                print(f"   ⏭️ Segment {i} déjà traité dans groupe, ignoré")
                continue
                
            elif i in segments_to_avoid:
                # Segment individuel à éviter (pas dans un groupe)
                print(f"   🚫 Évitement segment {i} : {segment['start_waypoint']}-{segment['end_waypoint']}")
                
                prev_free_segment = self._find_previous_free_segment(tollways_segments, i, segments_to_avoid)
                next_free_segment = self._find_next_free_segment(tollways_segments, i, segments_to_avoid)
                
                avoidance_segment = self._create_single_avoidance_segment(
                    segment, prev_free_segment, next_free_segment, route_coords
                )
                
                if avoidance_segment:
                    avoidance_segments.append(avoidance_segment)
                    current_position = avoidance_segment['end_coord']
                
                processed_segments.add(i)
                
            else:
                # Segment normal → Garder tel quel
                segment_coords = self._extract_segment_coordinates(segment, route_coords)
                if segment_coords:
                    normal_segment = {
                        'segment_type': 'normal',
                        'start': segment_coords[0],
                        'end': segment_coords[-1],
                        'start_coord': segment_coords[0],
                        'end_coord': segment_coords[-1],
                        'coordinates': segment_coords,
                        'original_segment': segment,
                        'description': f"Segment normal {i}"
                    }
                    avoidance_segments.append(normal_segment)
                    current_position = normal_segment['end_coord']
                
                processed_segments.add(i)
        
        print(f"   ✅ {len(avoidance_segments)} segments d'évitement créés")
        return avoidance_segments
    
    def _create_single_avoidance_segment(
        self, 
        avoid_segment: Dict,
        prev_free_segment: Optional[Dict],
        next_free_segment: Optional[Dict],
        route_coords: List[List[float]]
    ) -> Optional[Dict]:
        """
        Crée un segment d'évitement pour un segment payant donné.
        Utilise les 3 stratégies de fallback.
        """
        print(f"      🎯 Stratégies d'évitement pour segment {avoid_segment['start_waypoint']}-{avoid_segment['end_waypoint']}")
        
        # Stratégie 1 : Fin → Fin
        segment = self._try_end_to_end_avoidance(avoid_segment, prev_free_segment, next_free_segment, route_coords)
        if segment:
            print(f"      ✅ Stratégie 1 réussie (Fin → Fin)")
            return segment
        
        # Stratégie 2 : Début → Fin  
        segment = self._try_start_to_end_avoidance(avoid_segment, prev_free_segment, next_free_segment, route_coords)
        if segment:
            print(f"      ✅ Stratégie 2 réussie (Début → Fin)")
            return segment
        
        # Stratégie 3 : Sortie → Entrée
        segment = self._try_exit_to_entrance_avoidance(avoid_segment, prev_free_segment, next_free_segment, route_coords)
        if segment:
            print(f"      ✅ Stratégie 3 réussie (Sortie → Entrée)")
            return segment
        
        print(f"      ❌ Toutes les stratégies ont échoué pour ce segment")
        return None
    
    def _try_end_to_end_avoidance(
        self,
        avoid_segment: Dict,
        prev_free_segment: Optional[Dict],
        next_free_segment: Optional[Dict],
        route_coords: List[List[float]]
    ) -> Optional[Dict]:
        """Stratégie 1 : Fin du segment gratuit précédent → Fin du segment gratuit suivant."""
        if not prev_free_segment or not next_free_segment:
            return None
        
        try:
            # Coordonnées de fin des segments gratuits
            start_coord = route_coords[prev_free_segment['end_waypoint']]
            end_coord = route_coords[next_free_segment['end_waypoint']]
            
            # Calculer route sans péage
            avoidance_route = self.ors.get_route_avoid_tollways([start_coord, end_coord])
            
            if avoidance_route:
                return {
                    'segment_type': 'avoid_tolls',
                    'strategy': 'end_to_end',
                    'start': start_coord,
                    'end': end_coord,
                    'start_coord': start_coord,
                    'end_coord': end_coord,
                    'route': avoidance_route,
                    'avoided_segment': avoid_segment,
                    'description': f"Évitement sans péage (fin→fin)"
                }
        except Exception as e:
            print(f"         ⚠️ Erreur stratégie 1 : {e}")
        
        return None
    
    def _try_start_to_end_avoidance(
        self,
        avoid_segment: Dict,
        prev_free_segment: Optional[Dict],
        next_free_segment: Optional[Dict],
        route_coords: List[List[float]]
    ) -> Optional[Dict]:
        """Stratégie 2 : Début du segment gratuit précédent → Fin du segment gratuit suivant."""
        if not prev_free_segment or not next_free_segment:
            return None
        
        try:
            # Coordonnées de début/fin des segments gratuits
            start_coord = route_coords[prev_free_segment['start_waypoint']]
            end_coord = route_coords[next_free_segment['end_waypoint']]
            
            # Calculer route sans péage
            avoidance_route = self.ors.get_route_avoid_tollways([start_coord, end_coord])
            
            if avoidance_route:
                return {
                    'segment_type': 'avoid_tolls',
                    'strategy': 'start_to_end',
                    'start': start_coord,
                    'end': end_coord,
                    'start_coord': start_coord,
                    'end_coord': end_coord,
                    'route': avoidance_route,
                    'avoided_segment': avoid_segment,
                    'description': f"Évitement sans péage (début→fin)"
                }
        except Exception as e:
            print(f"         ⚠️ Erreur stratégie 2 : {e}")
        
        return None
    
    def _try_exit_to_entrance_avoidance(
        self,
        avoid_segment: Dict,
        prev_free_segment: Optional[Dict],
        next_free_segment: Optional[Dict],
        route_coords: List[List[float]]
    ) -> Optional[Dict]:
        """Stratégie 3 : Dernière sortie du segment précédent → Première entrée du segment suivant."""
        if not prev_free_segment or not next_free_segment:
            return None
        
        try:
            # Trouver la dernière sortie du segment précédent
            prev_segment_coords = self._extract_segment_coordinates(prev_free_segment, route_coords)
            exit_coord = self._find_last_exit_in_segment(prev_segment_coords)
            
            # Trouver la première entrée du segment suivant
            next_segment_coords = self._extract_segment_coordinates(next_free_segment, route_coords)
            entrance_coord = self._find_first_entrance_in_segment(next_segment_coords)
            
            if exit_coord and entrance_coord:
                # Calculer route sans péage
                avoidance_route = self.ors.get_route_avoid_tollways([exit_coord, entrance_coord])
                
                if avoidance_route:
                    return {
                        'segment_type': 'avoid_tolls',
                        'strategy': 'exit_to_entrance',
                        'start': exit_coord,
                        'end': entrance_coord,
                        'start_coord': exit_coord,
                        'end_coord': entrance_coord,
                        'route': avoidance_route,
                        'avoided_segment': avoid_segment,
                        'description': f"Évitement sans péage (sortie→entrée)"
                    }
        except Exception as e:
            print(f"         ⚠️ Erreur stratégie 3 : {e}")
        
        return None

    def _find_previous_free_segment(self, segments: List[Dict], current_index: int, segments_to_avoid: List[int] = None) -> Optional[Dict]:
        """
        Trouve le segment gratuit précédent.
        
        Args:
            segments: Liste des segments
            current_index: Index du segment courant
            segments_to_avoid: Liste des indices de segments à éviter (faux segments gratuits inclus)
        """
        segments_to_avoid = segments_to_avoid or []
        
        for i in range(current_index - 1, -1, -1):
            # Segment gratuit ET pas dans la liste à éviter
            if not segments[i].get('is_toll', False) and i not in segments_to_avoid:
                return segments[i]
        return None

    def _find_next_free_segment(self, segments: List[Dict], current_index: int, segments_to_avoid: List[int] = None) -> Optional[Dict]:
        """
        Trouve le segment gratuit suivant.
        
        Args:
            segments: Liste des segments
            current_index: Index du segment courant
            segments_to_avoid: Liste des indices de segments à éviter (faux segments gratuits inclus)
        """
        segments_to_avoid = segments_to_avoid or []
        
        for i in range(current_index + 1, len(segments)):
            # Segment gratuit ET pas dans la liste à éviter
            if not segments[i].get('is_toll', False) and i not in segments_to_avoid:
                return segments[i]
        return None
    
    def _find_previous_free_segment_index(self, segments: List[Dict], current_index: int, segments_to_avoid: List[int] = None) -> Optional[int]:
        """
        Trouve l'index du segment gratuit précédent (pour debug).
        """
        segments_to_avoid = segments_to_avoid or []
        
        for i in range(current_index - 1, -1, -1):
            if not segments[i].get('is_toll', False) and i not in segments_to_avoid:
                return i
        return None

    def _find_next_free_segment_index(self, segments: List[Dict], current_index: int, segments_to_avoid: List[int] = None) -> Optional[int]:
        """
        Trouve l'index du segment gratuit suivant (pour debug).
        """
        segments_to_avoid = segments_to_avoid or []
        
        for i in range(current_index + 1, len(segments)):
            if not segments[i].get('is_toll', False) and i not in segments_to_avoid:
                return i
        return None
    
    def _extract_segment_coordinates(self, segment: Dict, route_coords: List[List[float]]) -> List[List[float]]:
        """Extrait les coordonnées d'un segment."""
        start = segment['start_waypoint']
        end = segment['end_waypoint']
        
        if end >= len(route_coords):
            end = len(route_coords) - 1
        
        return route_coords[start:end + 1]
    
    def _find_last_exit_in_segment(self, segment_coords: List[List[float]]) -> Optional[List[float]]:
        """
        Trouve la dernière sortie (motorway_junction) dans un segment et retourne 
        le point final de sa motorway_link associée.
        """
        if not segment_coords:
            return None
        
        # Réutiliser le code de détection de sorties existant
        from src.services.toll.new_segmentation.exit_optimization.motorway_exit_finder import MotorwayExitFinder
        from src.cache import osm_data_cache
        
        exit_finder = MotorwayExitFinder(osm_data_cache._osm_parser)
        
        # Chercher des sorties dans une zone autour de la fin du segment
        segment_end = segment_coords[-1]
        exits_near_end = exit_finder.find_exits_near_point(segment_end, search_radius_km=2.0)
        
        if not exits_near_end:
            print(f"         ⚠️ Aucune sortie trouvée près de la fin du segment")
            return segment_coords[-1]  # Fallback sur le dernier point du segment
        
        # Prendre la dernière sortie (la plus proche de la fin du segment)
        last_exit = exits_near_end[0]  # déjà triées par distance
        
        # Récupérer le point final de la motorway_link
        exit_link_end_point = exit_finder.get_exit_link_last_point({'coordinates': last_exit.coordinates})
        
        print(f"         ✅ Dernière sortie trouvée : {last_exit.properties.get('name', 'sans nom')} → {exit_link_end_point}")
        return exit_link_end_point
    
    def _find_first_entrance_in_segment(self, segment_coords: List[List[float]]) -> Optional[List[float]]:
        """
        Trouve une junction d'entrée dans un segment et retourne ses coordonnées directement.
        
        IMPORTANT: Ce segment doit être un segment GRATUIT, pas un segment à éviter.
        Les coordonnées retournées doivent être sur la route principale pour que ORS puisse calculer.
        """
        if not segment_coords:
            return None
        
        print(f"         🔍 Recherche d'entrée dans segment de {len(segment_coords)} points")
        
        # Chercher toutes les motorway_junctions sur la route du segment
        from src.cache import osm_data_cache
        
        # Trouver les junctions dans un rayon élargi d'abord
        junctions_candidate = osm_data_cache._osm_parser.find_junctions_near_route(segment_coords, max_distance_km=1.0)
        
        # Filtrer strictement : garder seulement celles à moins de 10m de la route
        junctions_on_segment = []
        for junction in junctions_candidate:
            junction_coords = junction.coordinates
            min_distance_m = float('inf')
            
            # Trouver la distance minimale à la route
            for route_point in segment_coords:
                distance_m = self._calculate_distance_meters(junction_coords, route_point)
                min_distance_m = min(min_distance_m, distance_m)
            
            # Garder seulement si vraiment proche de la route (pas sur l'autre sens)
            if min_distance_m <= 10.0:  # 10m max au lieu de 1km
                junctions_on_segment.append(junction)
                print(f"         ✅ Junction gardée : {junction.properties.get('name', 'sans nom')} à {min_distance_m:.1f}m")
            else:
                print(f"         ❌ Junction écartée : {junction.properties.get('name', 'sans nom')} à {min_distance_m:.1f}m (trop loin)")
        
        print(f"         📊 {len(junctions_on_segment)}/{len(junctions_candidate)} junctions gardées après filtrage strict")
        
        if len(junctions_on_segment) < 2:
            if len(junctions_on_segment) == 1:
                print(f"         ⚠️ Une seule junction trouvée, utilisation comme entrée")
                entrance_junction = junctions_on_segment[0]
            else:
                print(f"         ⚠️ Aucune junction trouvée sur le segment")
                return segment_coords[0]  # Fallback sur le premier point du segment
        else:
            # Prendre la DEUXIÈME junction (index 1)
            entrance_junction = junctions_on_segment[1]
            print(f"         🎯 Utilisation de la 2ème junction comme entrée")
        
        # Retourner directement les coordonnées de la junction (pas le point final de motorway_link)
        entrance_coords = entrance_junction.coordinates
        
        print(f"         ✅ Entrée trouvée : {entrance_junction.properties.get('name', 'sans nom')} → {entrance_coords}")
        return entrance_coords
    
    def _calculate_distance_meters(self, coord1: List[float], coord2: List[float]) -> float:
        """
        Calcule la distance entre deux points en mètres.
        
        Args:
            coord1: Premier point [lon, lat]
            coord2: Deuxième point [lon, lat]
            
        Returns:
            float: Distance en mètres
        """
        import math
        
        lat1, lon1 = math.radians(coord1[1]), math.radians(coord1[0])
        lat2, lon2 = math.radians(coord2[1]), math.radians(coord2[0])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return 6371000.0 * c  # Rayon de la Terre en mètres
    
    def _group_consecutive_segments_to_avoid(self, segments_to_avoid: List[int]) -> List[List[int]]:
        """
        Regroupe les segments consécutifs à éviter.
        
        Args:
            segments_to_avoid: Liste des indices de segments à éviter
            
        Returns:
            List[List[int]]: Groupes de segments consécutifs
        """
        if not segments_to_avoid:
            return []
        
        # Trier les indices
        sorted_segments = sorted(segments_to_avoid)
        groups = []
        current_group = [sorted_segments[0]]
        
        for i in range(1, len(sorted_segments)):
            if sorted_segments[i] == sorted_segments[i-1] + 1:
                # Segment consécutif, ajouter au groupe actuel
                current_group.append(sorted_segments[i])
            else:
                # Gap détecté, commencer un nouveau groupe
                groups.append(current_group)
                current_group = [sorted_segments[i]]
        
        # Ajouter le dernier groupe
        groups.append(current_group)
        
        # Debug
        for i, group in enumerate(groups):
            if len(group) > 1:
                print(f"      📦 Groupe {i+1}: segments {group[0]}-{group[-1]} ({len(group)} segments)")
            else:
                print(f"      📦 Groupe {i+1}: segment {group[0]} (individuel)")
        
        return groups
    
    def _find_avoidance_group_for_segment(self, segment_index: int, avoidance_groups: List[List[int]]) -> Optional[List[int]]:
        """
        Trouve le groupe d'évitement contenant un segment donné.
        
        Args:
            segment_index: Index du segment
            avoidance_groups: Groupes d'évitement
            
        Returns:
            List[int]: Groupe contenant le segment, ou None
        """
        for group in avoidance_groups:
            if segment_index in group:
                return group
        return None
    
    def _create_grouped_avoidance_segment(
        self,
        avoidance_group: List[int],
        tollways_segments: List[Dict],
        route_coords: List[List[float]],
        segments_to_avoid: List[int]
    ) -> Optional[Dict]:
        """
        Crée un segment d'évitement pour un groupe de segments consécutifs.
        
        Args:
            avoidance_group: Indices des segments à éviter (consécutifs)
            tollways_segments: Tous les segments tollways
            route_coords: Coordonnées de la route
            segments_to_avoid: Tous les segments à éviter (pour éviter les faux segments gratuits)
            
        Returns:
            Dict: Segment d'évitement groupé ou None
        """
        if not avoidance_group:
            return None
        
        first_segment_idx = avoidance_group[0]
        last_segment_idx = avoidance_group[-1]
        
        print(f"      🔗 Création évitement groupé : segments {first_segment_idx} à {last_segment_idx}")
        
        # Trouver le segment gratuit avant le premier et après le dernier
        # En évitant les faux segments gratuits qui sont aussi dans segments_to_avoid
        prev_free_segment = self._find_previous_free_segment(tollways_segments, first_segment_idx, segments_to_avoid)
        next_free_segment = self._find_next_free_segment(tollways_segments, last_segment_idx, segments_to_avoid)
        
        if not prev_free_segment or not next_free_segment:
            print(f"      ❌ Pas de vrais segments gratuits adjacents trouvés")
            prev_idx = self._find_previous_free_segment_index(tollways_segments, first_segment_idx, segments_to_avoid)
            next_idx = self._find_next_free_segment_index(tollways_segments, last_segment_idx, segments_to_avoid)
            print(f"      📍 Segment gratuit précédent : {prev_idx}, suivant : {next_idx}")
            return None
        
        # Stratégie groupée : Fin du segment gratuit précédent → Début du segment gratuit suivant
        try:
            start_coord = route_coords[prev_free_segment['end_waypoint']]
            end_coord = route_coords[next_free_segment['start_waypoint']]
            
            print(f"      🎯 Évitement groupé : {start_coord} → {end_coord}")
            
            # Calculer route sans péage
            avoidance_route = self.ors.get_route_avoid_tollways([start_coord, end_coord])
            
            if avoidance_route:
                return {
                    'segment_type': 'avoid_tolls',
                    'strategy': 'grouped_avoidance',
                    'start': start_coord,
                    'end': end_coord,
                    'start_coord': start_coord,
                    'end_coord': end_coord,
                    'route': avoidance_route,
                    'avoided_segments': avoidance_group,
                    'description': f"Évitement groupé segments {first_segment_idx}-{last_segment_idx}"
                }
            else:
                print(f"      ❌ Impossible de calculer route d'évitement groupée")
                
        except Exception as e:
            print(f"      ❌ Erreur évitement groupé : {e}")
        
        return None
