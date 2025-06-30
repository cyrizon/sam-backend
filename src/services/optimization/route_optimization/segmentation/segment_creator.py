"""
Segment Creator
===============

Création des segments de route optimisés selon les péages sélectionnés.
ÉTAPE 6 de l'algorithme d'optimisation.
"""

from typing import List, Dict, Tuple


class SegmentCreator:
    """
    Créateur de segments optimisés.
    Responsabilité : ÉTAPE 6 de l'algorithme d'optimisation.
    """
    
    def __init__(self):
        """Initialise le créateur de segments."""
        pass
    
    def create_optimized_segments(
        self,
        coordinates: List[List[float]],
        selected_tolls: List,
        identification_result: Dict,
        selection_result: Dict
    ) -> List[Dict]:
        """
        ÉTAPE 6: Crée les segments optimisés pour le calcul de routes.
        
        Args:
            coordinates: Coordonnées [départ, arrivée]
            selected_tolls: Péages sélectionnés à utiliser
            identification_result: Résultat de l'identification (étape 3)
            selection_result: Résultat de la sélection (étape 5)
            
        Returns:
            Liste des segments à calculer avec points de passage
        """
        print("🏗️ Étape 6: Création des segments optimisés...")
        print(f"   📊 {len(selected_tolls)} péages sélectionnés")
        
        start_point = coordinates[0]
        end_point = coordinates[-1]
        
        # 1. Pas de péages → segment sans péage
        if not selected_tolls:
            return self._create_no_toll_segment(start_point, end_point)
        
        # 2. Parcourir selection_result pour créer les segments
        segments_data = selection_result.get('segments', [])
        
        if segments_data:
            # On a des segments définis dans selection_result
            return self._create_segments_from_selection(segments_data)
        else:
            # Fallback : segment simple avec tous les péages
            return self._create_simple_segment_with_tolls(start_point, end_point, selected_tolls)
    
    def _create_no_toll_segment(self, start_point: List[float], end_point: List[float]) -> List[Dict]:
        """Crée un segment simple sans péage."""
        print("   🚫 Segment sans péage")
        
        return [{
            'segment_id': 0,
            'segment_type': 'no_tolls',
            'start_point': start_point,
            'end_point': end_point,
            'waypoints': [start_point, end_point],
            'avoid_tolls': True,
            'force_tolls': [],
            'optimization_hints': ['avoid_all_tolls']
        }]
    
    def _create_segments_from_selection(self, segments_data: List[Dict]) -> List[Dict]:
        """
        Crée les segments à partir des données de selection_result.
        Format attendu : [[Départ->péageX, avec péage], [péageX->sortieX, avec péage], [sortieX->arrivée, sans péage]]
        
        Args:
            segments_data: Données des segments depuis selection_result
            
        Returns:
            Liste des segments formatés
        """
        print(f"   � Création de {len(segments_data)} segments depuis selection_result")
        
        segments = []
        
        for i, segment_info in enumerate(segments_data):
            # Extraire les coordonnées et le flag péage
            start_coord = segment_info.get('start_point')
            end_coord = segment_info.get('end_point')
            has_toll = segment_info.get('has_toll', False)
            toll_info = segment_info.get('toll_info', {})
            
            # Créer le segment
            segment = {
                'segment_id': i,
                'segment_type': 'with_tolls' if has_toll else 'no_tolls',
                'start_point': start_coord,
                'end_point': end_coord,
                'waypoints': [start_coord, end_coord],
                'avoid_tolls': not has_toll,
                'force_tolls': [toll_info] if has_toll and toll_info else [],
                'optimization_hints': ['use_tolls'] if has_toll else ['avoid_tolls']
            }
            
            segments.append(segment)
            
            print(f"     Segment {i}: {start_coord} -> {end_coord} ({'avec' if has_toll else 'sans'} péage)")
        
        return segments
    
    def _create_simple_segment_with_tolls(
        self, 
        start_point: List[float], 
        end_point: List[float], 
        selected_tolls: List
    ) -> List[Dict]:
        """
        Crée un segment simple avec tous les péages sélectionnés.
        Fallback quand on n'a pas de segments définis.
        
        Args:
            start_point: Point de départ
            end_point: Point d'arrivée
            selected_tolls: Péages sélectionnés
            
        Returns:
            Segment unique avec tous les péages
        """
        print("   📍 Segment simple avec tous les péages")
        
        return [{
            'segment_id': 0,
            'segment_type': 'simple_with_tolls',
            'start_point': start_point,
            'end_point': end_point,
            'waypoints': [start_point, end_point],
            'avoid_tolls': False,
            'force_tolls': selected_tolls,
            'optimization_hints': ['use_selected_tolls']
        }]
