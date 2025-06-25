"""
tollways_analyzer.py
------------------

Analyseur de segments tollways pour identifier où sont situés les péages
et déterminer la stratégie d'évitement optimale.

Responsabilité unique :
- Analyser les segments tollways d'ORS
- Identifier quels péages sont sur quels segments
- Détecter les cas multi-péages sur même segment
"""

from typing import List, Dict, Tuple
from src.services.toll.new_segmentation.toll_matcher import MatchedToll


class TollwaysAnalyzer:
    """Analyse les segments tollways pour optimiser la segmentation."""
    
    def analyze_segments_for_tolls(
        self, 
        tollways_segments: List[Dict], 
        tolls_on_route: List[MatchedToll], 
        route_coords: List[List[float]]
    ) -> Dict:
        """
        Analyse les segments tollways pour identifier où sont les péages.
        
        Args:
            tollways_segments: Segments extraits d'ORS
            tolls_on_route: Péages détectés sur la route
            route_coords: Coordonnées de la route complète
            
        Returns:
            Dict contenant l'analyse des segments et péages
        """
        print("🔍 Analyse des segments tollways vs péages...")
        
        analysis = {
            'segments_with_tolls': [],
            'free_segments': [],
            'multi_toll_segments': [],
            'single_toll_segments': [],
            'problematic_segments': []
        }
        
        for i, segment in enumerate(tollways_segments):
            if segment['is_toll']:
                # Trouver quels péages sont dans ce segment
                tolls_in_segment = self._find_tolls_in_segment(segment, tolls_on_route, route_coords)
                
                segment_info = {
                    'segment_index': i,
                    'segment': segment,
                    'tolls': tolls_in_segment,
                    'toll_count': len(tolls_in_segment)
                }
                
                analysis['segments_with_tolls'].append(segment_info)
                
                if len(tolls_in_segment) == 1:
                    analysis['single_toll_segments'].append(segment_info)
                elif len(tolls_in_segment) > 1:
                    analysis['multi_toll_segments'].append(segment_info)
                    analysis['problematic_segments'].append(segment_info)
                    
            else:
                analysis['free_segments'].append({
                    'segment_index': i,
                    'segment': segment
                })
        
        print(f"   📊 Segments analysés :")
        print(f"      - Gratuits : {len(analysis['free_segments'])}")
        print(f"      - Payants : {len(analysis['segments_with_tolls'])}")
        print(f"      - Multi-péages : {len(analysis['multi_toll_segments'])}")
        
        return analysis
    
    def _find_tolls_in_segment(
        self, 
        segment: Dict, 
        tolls: List[MatchedToll], 
        route_coords: List[List[float]]
    ) -> List[MatchedToll]:
        """Trouve quels péages sont dans un segment donné."""
        start_waypoint = segment['start_waypoint']
        end_waypoint = segment['end_waypoint']
        
        # Vérifier que les indices sont valides
        if end_waypoint >= len(route_coords):
            return []
        
        tolls_in_segment = []
        
        for toll in tolls:
            toll_coords = toll.osm_coordinates or toll.csv_coordinates
            if not toll_coords:
                continue
                
            # Trouver la position du péage sur la route
            toll_position = self._find_toll_position_on_route(toll_coords, route_coords)
            
            # Vérifier si le péage est dans le segment
            if start_waypoint <= toll_position <= end_waypoint:
                tolls_in_segment.append(toll)
        
        return tolls_in_segment
    
    def _find_toll_position_on_route(
        self, 
        toll_coords: List[float], 
        route_coords: List[List[float]]
    ) -> int:
        """Trouve la position approximative d'un péage sur la route."""
        min_distance = float('inf')
        closest_index = 0
        
        for i, coord in enumerate(route_coords):
            distance = self._calculate_distance(toll_coords, coord)
            if distance < min_distance:
                min_distance = distance
                closest_index = i
        
        return closest_index
    
    def _calculate_distance(self, point1: List[float], point2: List[float]) -> float:
        """Calcule la distance entre deux points (approximation simple)."""
        lat_diff = point1[1] - point2[1]
        lon_diff = point1[0] - point2[0]
        return (lat_diff ** 2 + lon_diff ** 2) ** 0.5
    
    def identify_avoidance_strategy(
        self, 
        analysis: Dict, 
        selected_tolls: List[MatchedToll]
    ) -> Dict:
        """
        Identifie la stratégie d'évitement pour chaque péage à éviter.
        
        Args:
            analysis: Résultat de l'analyse des segments
            selected_tolls: Péages sélectionnés à utiliser
            
        Returns:
            Dict avec les stratégies d'évitement
        """
        print("🎯 Identification des stratégies d'évitement...")
        
        selected_names = [toll.effective_name for toll in selected_tolls]
        strategies = {
            'tollways_based': [],    # Utiliser les segments gratuits
            'exit_optimization': [], # Optimiser les sorties
            'segments_to_avoid': []  # Segments à éviter complètement
        }
        
        for segment_info in analysis['segments_with_tolls']:
            segment_tolls = segment_info['tolls']
            
            # Péages à utiliser et à éviter dans ce segment
            tolls_to_use = [t for t in segment_tolls if t.effective_name in selected_names]
            tolls_to_avoid = [t for t in segment_tolls if t.effective_name not in selected_names]
            
            if not tolls_to_avoid:
                # Aucun péage à éviter dans ce segment
                continue
                
            if len(segment_tolls) == 1:
                # Un seul péage dans le segment à éviter → Utiliser tollways
                strategies['tollways_based'].append({
                    'segment_info': segment_info,
                    'tolls_to_avoid': tolls_to_avoid,
                    'method': 'skip_segment'
                })
                strategies['segments_to_avoid'].append(segment_info['segment'])
                
            else:
                # Plusieurs péages dans le segment → Cas complexe
                if tolls_to_use:
                    # On doit utiliser un péage mais en éviter d'autres
                    strategies['exit_optimization'].append({
                        'segment_info': segment_info,
                        'tolls_to_use': tolls_to_use,
                        'tolls_to_avoid': tolls_to_avoid,
                        'method': 'optimize_exit'
                    })
                else:
                    # Éviter tout le segment
                    strategies['tollways_based'].append({
                        'segment_info': segment_info,
                        'tolls_to_avoid': tolls_to_avoid,
                        'method': 'skip_segment'
                    })
                    strategies['segments_to_avoid'].append(segment_info['segment'])
        
        print(f"   📋 Stratégies identifiées :")
        print(f"      - Évitement tollways : {len(strategies['tollways_based'])}")
        print(f"      - Optimisation sortie : {len(strategies['exit_optimization'])}")
        
        return strategies
