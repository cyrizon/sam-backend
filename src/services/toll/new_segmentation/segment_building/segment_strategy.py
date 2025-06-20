"""
segment_strategy.py
------------------

Module pour la logique de stratégie de construction des segments.
Responsabilité : déterminer comment construire les segments selon les règles métier.
"""

from typing import List, Dict
from ..toll_matcher import MatchedToll


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
                from .toll_positioning import TollPositioning
                toll_positioning = TollPositioning()
                
                tolls_before = toll_positioning.get_tolls_before(current_toll, all_tolls)
                if tolls_before:
                    # Éviter les péages avant : Départ → Entrée avant péage
                    entrance_coords = self.entrance_exit_finder.find_entrance_coordinates(current_toll)
                    segment = {
                        'type': 'avoid_tolls',
                        'start': current_point,
                        'end': entrance_coords,
                        'description': f"Départ vers entrée {current_toll.effective_name} (évite {len(tolls_before)} péages)"
                    }
                    segments.append(segment)
                    current_point = entrance_coords
                    print(f"   📍 Segment {len(segments)} : Départ → Entrée {current_toll.effective_name} (évite {len(tolls_before)} péages)")
                    
                    # Entrée → Péage
                    segment = {
                        'type': 'normal',
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
                        'type': 'normal',
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
                    'type': 'normal',
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
                from .toll_positioning import TollPositioning
                toll_positioning = TollPositioning()
                
                tolls_after = toll_positioning.get_tolls_after(current_toll, all_tolls)
                if tolls_after:
                    # Éviter les péages après : Péage → Sortie, puis Sortie → Arrivée
                    from .exit_finder import ExitFinder
                    exit_finder = ExitFinder(self.entrance_exit_finder, self.junction_analyzer)
                    
                    exit_coords = exit_finder.find_optimal_exit_after_toll(current_toll, tolls_after, route_coords)
                    
                    # Péage → Sortie
                    segment = {
                        'type': 'normal',
                        'start': current_point,
                        'end': exit_coords,
                        'description': f"{current_toll.effective_name} vers sortie"
                    }
                    segments.append(segment)
                    current_point = exit_coords
                    print(f"   📍 Segment {len(segments)} : {current_toll.effective_name} → Sortie")
                    
                    # Sortie → Arrivée
                    segment = {
                        'type': 'avoid_tolls',
                        'start': current_point,
                        'end': end_coords,
                        'description': f"Sortie vers arrivée (évite {len(tolls_after)} péages)"
                    }
                    segments.append(segment)
                    print(f"   📍 Segment {len(segments)} : Sortie → Arrivée (évite {len(tolls_after)} péages)")
                else:
                    # Pas de péages après : Péage → Arrivée directement
                    segment = {
                        'type': 'normal',
                        'start': current_point,
                        'end': end_coords,
                        'description': f"{current_toll.effective_name} vers arrivée"
                    }
                    segments.append(segment)
                    print(f"   📍 Segment {len(segments)} : {current_toll.effective_name} → Arrivée")
            else:
                # Péage intermédiaire : vérifier s'il faut sortir
                next_toll = selected_tolls[i + 1]
                from .toll_positioning import TollPositioning
                toll_positioning = TollPositioning()
                
                tolls_between = toll_positioning.get_tolls_between(current_toll, next_toll, all_tolls)
                
                if tolls_between:
                    # Il y a des péages à éviter : Péage → Sortie, puis Sortie → Entrée suivant
                    from .exit_finder import ExitFinder
                    exit_finder = ExitFinder(self.entrance_exit_finder, self.junction_analyzer)
                    
                    exit_coords = exit_finder.find_optimal_exit_after_toll(current_toll, tolls_between, route_coords)
                    entrance_coords = self.entrance_exit_finder.find_entrance_coordinates(next_toll)
                    
                    # Péage → Sortie
                    segment = {
                        'type': 'normal',
                        'start': current_point,
                        'end': exit_coords,
                        'description': f"{current_toll.effective_name} vers sortie"
                    }
                    segments.append(segment)
                    current_point = exit_coords
                    print(f"   📍 Segment {len(segments)} : {current_toll.effective_name} → Sortie")
                    
                    # Sortie → Entrée suivant
                    segment = {
                        'type': 'avoid_tolls',
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
