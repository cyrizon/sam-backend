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
from src.services.toll.new_segmentation.toll_matcher import MatchedToll


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
        
        avoidance_segments = []
        current_position = start_coord
        
        for i, segment in enumerate(tollways_segments):
            print(f"   🔍 DEBUG: Segment {i}, à éviter ? {i in segments_to_avoid}")
            if i in segments_to_avoid:  # Comparer l'index, pas l'objet segment
                # Segment à éviter → Créer un segment d'évitement
                print(f"   🚫 Évitement segment {i} : {segment['start_waypoint']}-{segment['end_waypoint']}")
                
                # Trouver le segment gratuit précédent et suivant
                prev_free_segment = self._find_previous_free_segment(tollways_segments, i)
                next_free_segment = self._find_next_free_segment(tollways_segments, i)
                
                avoidance_segment = self._create_single_avoidance_segment(
                    segment, prev_free_segment, next_free_segment, route_coords
                )
                
                if avoidance_segment:
                    avoidance_segments.append(avoidance_segment)
                    current_position = avoidance_segment['end_coord']
                
            else:
                # Segment normal → Garder tel quel
                segment_coords = self._extract_segment_coordinates(segment, route_coords)
                if segment_coords:
                    normal_segment = {
                        'type': 'normal',
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
                    'type': 'avoid_tolls',
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
                    'type': 'avoid_tolls',
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
                        'type': 'avoid_tolls',
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
    
    def _find_previous_free_segment(self, segments: List[Dict], current_index: int) -> Optional[Dict]:
        """Trouve le segment gratuit précédent."""
        for i in range(current_index - 1, -1, -1):
            if not segments[i]['is_toll']:  # Segment gratuit si NOT is_toll
                return segments[i]
        return None
    
    def _find_next_free_segment(self, segments: List[Dict], current_index: int) -> Optional[Dict]:
        """Trouve le segment gratuit suivant."""
        for i in range(current_index + 1, len(segments)):
            if not segments[i]['is_toll']:  # Segment gratuit si NOT is_toll
                return segments[i]
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
        from src.services.osm_data_cache import osm_data_cache
        
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
        Trouve la DEUXIÈME motorway_junction dans un segment et retourne ses coordonnées directement.
        
        Logique :
        - Première junction = Sortie + Entrée proche (souvent après la sortie) ❌
        - Deuxième junction = Entrée plus loin → ORS peut calculer un itinéraire valide ✅
        - On prend directement le point junction (pas le point final de motorway_link)
        """
        if not segment_coords:
            return None
        
        # Chercher toutes les motorway_junctions sur la route du segment
        from src.services.osm_data_cache import osm_data_cache
        
        # Trouver les junctions sur ce segment de route
        junctions_on_segment = osm_data_cache._osm_parser.find_junctions_near_route(segment_coords, max_distance_km=1.0)
        
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
