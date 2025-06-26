"""
segment_strategy.py
------------------

Module pour la logique de stratégie de construction des segments.
Responsabilité : déterminer comment construire les segments selon les règles métier.
"""

from typing import List, Dict
from ..toll_matcher import MatchedToll
from .toll_positioning import TollPositioning
from .strategic_entrance_finder import StrategicEntranceFinder
from .exit_finder import ExitFinder


class SegmentStrategy:
    """
    Gère la logique de stratégie pour la construction des segments intelligents.
    
    Règles métier :
    - Segment vers péage seulement si nécessaire
    - Segment péage → sortie SEULEMENT si péages à éviter après
    - Segment sortie → entrée pour éviter des péages
    - Segment entrée → péage si nécessaire
    """
    
    def __init__(self, entrance_exit_finder, junction_analyzer=None):
        """
        Initialise la stratégie avec les outils nécessaires.
        
        Args:
            entrance_exit_finder: Finder pour les entrées/sorties
            junction_analyzer: Analyzer pour les junctions (optionnel)
        """
        self.entrance_exit_finder = entrance_exit_finder
        self.junction_analyzer = junction_analyzer
    
    def build_granular_segments(
        self,
        start_coords: List[float],
        end_coords: List[float], 
        all_tolls: List[MatchedToll],
        selected_tolls: List[MatchedToll],
        route_coords: List[List[float]]
    ) -> List[Dict]:
        """
        Construit les segments avec la logique granulaire.
        
        Logique :
        - Départ → Premier péage (évite péages avant si nécessaire)
        - Pour chaque péage sélectionné :
          * Si péages à éviter après : Péage → Sortie, puis Sortie → Prochain point
          * Sinon : Péage → Prochain péage directement
        - Dernier péage → Arrivée
        """
        segments = []
        current_point = start_coords
        
        for i, current_toll in enumerate(selected_tolls):
            is_first = (i == 0)
            is_last = (i == len(selected_tolls) - 1)
            # 1. Segment vers le péage actuel (si nécessaire)
            if is_first:
                # Premier péage : gérer l'évitement des péages avant
                toll_positioning = TollPositioning()
                
                tolls_before = toll_positioning.get_tolls_before(current_toll, all_tolls)
                if tolls_before:
                    # Éviter les péages avant : Départ → Entrée stratégique avant péage
                    strategic_finder = StrategicEntranceFinder(self.entrance_exit_finder, self.junction_analyzer)
                    
                    entrance_coords = strategic_finder.find_strategic_entrance_before_toll(
                        current_toll, tolls_before, route_coords
                    )
                    segment = {
                        'segment_type': 'avoid_tolls',
                        'start': current_point,
                        'end': entrance_coords,
                        'description': f"Départ vers entrée stratégique {current_toll.effective_name} (évite {len(tolls_before)} péages)"
                    }
                    segments.append(segment)
                    current_point = entrance_coords
                    print(f"   📍 Segment {len(segments)} : Départ → Entrée {current_toll.effective_name} (évite {len(tolls_before)} péages)")
                    
                    # Entrée → Péage
                    segment = {
                        'segment_type': 'normal',
                        'start': current_point,
                        'end': current_toll.osm_coordinates,
                        'description': f"Entrée vers {current_toll.effective_name}"
                    }
                    segments.append(segment)
                    current_point = current_toll.osm_coordinates
                    print(f"   📍 Segment {len(segments)} : Entrée → {current_toll.effective_name}")
                else:
                    # Pas de péages avant : Départ → Péage directement
                    segment = {
                        'segment_type': 'normal',
                        'start': current_point,
                        'end': current_toll.osm_coordinates,
                        'description': f"Départ vers {current_toll.effective_name}"
                    }
                    segments.append(segment)
                    current_point = current_toll.osm_coordinates
                    print(f"   📍 Segment {len(segments)} : Départ → {current_toll.effective_name}")
            else:
                # Péage intermédiaire : on y arrive depuis le point précédent
                segment = {
                    'segment_type': 'normal',
                    'start': current_point,
                    'end': current_toll.osm_coordinates,
                    'description': f"Vers {current_toll.effective_name}"
                }
                segments.append(segment)
                current_point = current_toll.osm_coordinates
                print(f"   📍 Segment {len(segments)} : → {current_toll.effective_name}")
            
            # 2. Segment après le péage (sortie si nécessaire)
            if is_last:
                # Dernier péage : gérer l'évitement des péages après
                toll_positioning = TollPositioning()
                
                tolls_after = toll_positioning.get_tolls_after(current_toll, all_tolls)
                if tolls_after:
                    # Éviter les péages après : Péage → Sortie, puis Sortie → Arrivée
                    exit_finder = ExitFinder(self.entrance_exit_finder, self.junction_analyzer)
                    
                    exit_coords = exit_finder.find_optimal_exit_after_toll(current_toll, tolls_after, route_coords)
                    
                    # Péage → Sortie
                    segment = {
                        'segment_type': 'normal',
                        'start': current_point,
                        'end': exit_coords,
                        'description': f"{current_toll.effective_name} vers sortie"
                    }
                    segments.append(segment)
                    current_point = exit_coords
                    print(f"   📍 Segment {len(segments)} : {current_toll.effective_name} → Sortie")
                    
                    # Sortie → Arrivée
                    segment = {
                        'segment_type': 'avoid_tolls',
                        'start': current_point,
                        'end': end_coords,
                        'description': f"Sortie vers arrivée (évite {len(tolls_after)} péages)"
                    }
                    segments.append(segment)
                    print(f"   📍 Segment {len(segments)} : Sortie → Arrivée (évite {len(tolls_after)} péages)")
                else:
                    # Pas de péages après : Péage → Arrivée directement
                    segment = {
                        'segment_type': 'normal',
                        'start': current_point,
                        'end': end_coords,
                        'description': f"{current_toll.effective_name} vers arrivée"
                    }
                    segments.append(segment)
                    print(f"   📍 Segment {len(segments)} : {current_toll.effective_name} → Arrivée")
            else:
                # Péage intermédiaire : vérifier s'il faut sortir
                next_toll = selected_tolls[i + 1]
                toll_positioning = TollPositioning()
                
                tolls_between = toll_positioning.get_tolls_between(current_toll, next_toll, all_tolls)
                
                if tolls_between:
                    # Il y a des péages à éviter : Péage → Sortie, puis Sortie → Entrée suivant
                    exit_finder = ExitFinder(self.entrance_exit_finder, self.junction_analyzer)
                    
                    exit_coords = exit_finder.find_optimal_exit_after_toll(current_toll, tolls_between, route_coords)
                    entrance_coords = self.entrance_exit_finder.find_entrance_coordinates(next_toll)
                    
                    # Péage → Sortie
                    segment = {
                        'segment_type': 'normal',
                        'start': current_point,
                        'end': exit_coords,
                        'description': f"{current_toll.effective_name} vers sortie"
                    }
                    segments.append(segment)
                    current_point = exit_coords
                    print(f"   📍 Segment {len(segments)} : {current_toll.effective_name} → Sortie")
                    
                    # Sortie → Entrée suivant
                    segment = {
                        'segment_type': 'avoid_tolls',
                        'start': current_point,
                        'end': entrance_coords,
                        'description': f"Sortie vers entrée {next_toll.effective_name} (évite {len(tolls_between)} péages)"
                    }
                    segments.append(segment)
                    current_point = entrance_coords
                    print(f"   📍 Segment {len(segments)} : Sortie → Entrée {next_toll.effective_name} (évite {len(tolls_between)} péages)")
                else:
                    # Pas de péages entre : continuer directement vers le suivant
                    current_point = current_toll.osm_coordinates
                    print(f"   📍 Continue directement vers {next_toll.effective_name}")
        
        return segments
