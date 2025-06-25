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
        
        # Détecter les segments "faux gratuits" entre péages fermés
        fake_free_segments = self._detect_fake_free_segments(analysis, selected_tolls)
        
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
        
        # Forcer l'optimisation de sortie pour les segments "faux gratuits"
        self._apply_fake_free_segment_fix(strategies, fake_free_segments, selected_tolls)
        
        print(f"   📋 Stratégies identifiées :")
        print(f"      - Évitement tollways : {len(strategies['tollways_based'])}")
        print(f"      - Optimisation sortie : {len(strategies['exit_optimization'])}")
        print(f"      - Segments faux gratuits détectés : {len(fake_free_segments)}")
        
        return strategies
    
    def _detect_fake_free_segments(
        self, 
        analysis: Dict, 
        selected_tolls: List[MatchedToll]
    ) -> List[Dict]:
        """
        Détecte les segments "gratuits" qui sont en fait entre deux péages fermés
        et ne peuvent donc pas être utilisés pour l'évitement.
        """
        print("🕵️ Détection des segments faux gratuits entre péages fermés...")
        
        fake_free_segments = []
        all_tolls = []
        
        # Collecter tous les péages avec leur position
        for segment_info in analysis['segments_with_tolls']:
            for toll in segment_info['tolls']:
                all_tolls.append({
                    'toll': toll,
                    'segment_index': segment_info['segment_index'],
                    'is_closed_system': self._is_closed_system_toll(toll)
                })
        
        # Trier les péages par position sur la route
        all_tolls.sort(key=lambda x: x['segment_index'])
        
        # Vérifier chaque segment gratuit
        for free_segment in analysis['free_segments']:
            segment_index = free_segment['segment_index']
            
            # Trouver les péages avant et après ce segment
            peages_before = [t for t in all_tolls if t['segment_index'] < segment_index]
            peages_after = [t for t in all_tolls if t['segment_index'] > segment_index]
            
            if peages_before and peages_after:
                # Péage fermé le plus proche avant
                closest_before = max(peages_before, key=lambda x: x['segment_index'])
                # Péage fermé le plus proche après
                closest_after = min(peages_after, key=lambda x: x['segment_index'])
                
                # Si les deux péages les plus proches sont fermés
                if closest_before['is_closed_system'] and closest_after['is_closed_system']:
                    fake_free_segments.append({
                        'segment': free_segment,
                        'peage_before': closest_before['toll'],
                        'peage_after': closest_after['toll']
                    })
                    
                    print(f"   ⚠️ Segment faux gratuit détecté entre :")
                    print(f"      - {closest_before['toll'].effective_name} (fermé)")
                    print(f"      - {closest_after['toll'].effective_name} (fermé)")
        
        return fake_free_segments
    
    def _is_closed_system_toll(self, toll: MatchedToll) -> bool:
        """Détermine si un péage est un système fermé (F) ou ouvert (O)."""
        # Utiliser l'attribut csv_role du MatchedToll (provenant du CSV matching)
        # F = fermé (closed system), O = ouvert (open system)
        if hasattr(toll, 'csv_role') and toll.csv_role:
            return toll.csv_role.upper() == 'F'
        
        # Si pas de csv_role, considérer comme ouvert par défaut (permet l'évitement)
        return False
    
    def _apply_fake_free_segment_fix(
        self, 
        strategies: Dict, 
        fake_free_segments: List[Dict], 
        selected_tolls: List[MatchedToll]
    ):
        """
        Applique la correction pour les segments faux gratuits en forçant
        l'utilisation de l'optimisation de sortie au lieu de l'évitement tollways.
        """
        if not fake_free_segments:
            return
        
        print("🔧 Application de la correction pour segments faux gratuits...")
        
        selected_names = [toll.effective_name for toll in selected_tolls]
        
        for fake_segment_info in fake_free_segments:
            peage_before = fake_segment_info['peage_before']
            peage_after = fake_segment_info['peage_after']
            
            # Si ces péages sont dans notre sélection, forcer l'optimisation de sortie
            # pour gérer le passage entre eux
            peages_to_handle = []
            if peage_before.effective_name in selected_names:
                peages_to_handle.append(peage_before)
            if peage_after.effective_name in selected_names:
                peages_to_handle.append(peage_after)
            
            if peages_to_handle:
                # Créer une stratégie d'optimisation de sortie pour ces péages
                strategies['exit_optimization'].append({
                    'segment_info': None,  # Pas de segment spécifique
                    'tolls_to_use': peages_to_handle,
                    'tolls_to_avoid': [],
                    'method': 'handle_closed_system_transition',
                    'reason': f'Transition entre péages fermés {peage_before.effective_name} → {peage_after.effective_name}'
                })
                
                print(f"   ✅ Correction appliquée pour transition :")
                print(f"      {peage_before.effective_name} → {peage_after.effective_name}")

        return strategies
