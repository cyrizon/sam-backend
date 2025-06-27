"""
segment_builders.py
------------------

Module pour les méthodes de construction de segments spécialisés.
Responsabilité : créer différents types de segments selon les contextes spécifiques.
"""

from typing import List, Dict
from src.cache.models.matched_toll import MatchedToll
from .toll_positioning import TollPositioning
from .exit_finder import ExitFinder


class SegmentBuilders:
    """
    Collection de méthodes pour construire des segments spécialisés.
    """
    
    def __init__(self, entrance_exit_finder, junction_analyzer=None):
        """
        Initialise les builders avec les outils nécessaires.
        
        Args:
            entrance_exit_finder: Finder pour les entrées/sorties
            junction_analyzer: Analyzer pour les junctions (optionnel)
        """
        self.entrance_exit_finder = entrance_exit_finder
        self.junction_analyzer = junction_analyzer
        self.toll_positioning = TollPositioning()
        self.exit_finder = ExitFinder(entrance_exit_finder, junction_analyzer)
    
    def build_first_segment(
        self, 
        start_coords: List[float], 
        first_toll: MatchedToll,
        all_tolls: List[MatchedToll],
        route_coords: List[List[float]] = None
    ) -> Dict:
        """
        Construit le premier segment : départ → premier péage.
        Utilise les vraies motorway_junctions pour éviter les péages précédents.
        
        Args:
            start_coords: Coordonnées de départ
            first_toll: Premier péage sélectionné
            all_tolls: Tous les péages sur la route
            route_coords: Coordonnées de la route de base
            
        Returns:
            Dict: Segment de route
        """        
        # Vérifier s'il y a des péages à éviter avant le premier péage
        tolls_before = self.toll_positioning.get_tolls_before(first_toll, all_tolls)
        
        if tolls_before and self.junction_analyzer and route_coords:
            # Utiliser l'analyzer pour trouver la vraie sortie avant le premier péage
            exit_junction = self.junction_analyzer.find_exit_before_toll(
                route_coords, first_toll, tolls_before
            )
            
            if exit_junction:
                # Quand on trouve une sortie, on va directement à l'entrée du péage sélectionné
                # pour éviter les segments manquants
                entrance_coords = self.entrance_exit_finder.find_entrance_coordinates(first_toll)
                segment_type = 'avoid_tolls'
                end_coords = entrance_coords
                print(f"   📍 Segment 1 : Départ → Entrée {first_toll.effective_name} (évite {len(tolls_before)} péages via sortie {exit_junction['name']})")
                
                # Stocker la sortie optimale pour utilisation ultérieure si nécessaire
                setattr(self, '_exit_before_first_toll', exit_junction)
            else:
                # Fallback vers la méthode classique
                entrance_coords = self.entrance_exit_finder.find_entrance_coordinates(first_toll)
                segment_type = 'avoid_tolls'
                end_coords = entrance_coords
                print(f"   📍 Segment 1 : Départ → Entrée {first_toll.effective_name} (évite {len(tolls_before)} péages - fallback)")
        else:
            # Route normale jusqu'au péage
            segment_type = 'normal'
            end_coords = first_toll.osm_coordinates
            print(f"   📍 Segment 1 : Départ → {first_toll.effective_name} (route normale)")
        
        return {
            'segment_type': segment_type,
            'start': start_coords,
            'end': end_coords,
            'description': f"Départ vers {first_toll.effective_name}"
        }
    
    def build_intermediate_segment(
        self, 
        previous_toll: MatchedToll, 
        current_toll: MatchedToll,
        all_tolls: List[MatchedToll]
    ) -> Dict:
        """
        Construit un segment intermédiaire : péage précédent → péage actuel.
        
        Args:
            previous_toll: Péage précédent
            current_toll: Péage actuel
            all_tolls: Tous les péages sur la route
            
        Returns:
            Dict: Segment de route
        """
        # Trouver les péages entre les deux péages sélectionnés
        tolls_between = self.toll_positioning.get_tolls_between(previous_toll, current_toll, all_tolls)
        
        if tolls_between:
            # Éviter les péages intermédiaires : sortie précédent → entrée actuel
            exit_coords = self.entrance_exit_finder.find_exit_coordinates(previous_toll)
            entrance_coords = self.entrance_exit_finder.find_entrance_coordinates(current_toll)
            
            segment_type = 'avoid_tolls'
            start_coords = exit_coords
            end_coords = entrance_coords
            print(f"   📍 Segment : Sortie {previous_toll.effective_name} → Entrée {current_toll.effective_name} (évite {len(tolls_between)} péages)")
        else:
            # Route normale entre les deux péages
            segment_type = 'normal'
            start_coords = previous_toll.osm_coordinates
            end_coords = current_toll.osm_coordinates
            print(f"   📍 Segment : {previous_toll.effective_name} → {current_toll.effective_name} (route normale)")
        
        return {
            'segment_type': segment_type,
            'start': start_coords,
            'end': end_coords,
            'description': f"{previous_toll.effective_name} vers {current_toll.effective_name}"
        }
    
    def build_last_segment(
        self, 
        last_toll: MatchedToll, 
        end_coords: List[float], 
        all_tolls: List[MatchedToll],
        route_coords: List[List[float]] = None
    ) -> Dict:
        """
        Construit le dernier segment : dernier péage → arrivée.
        IMPORTANT : Vérifie s'il y a des péages à éviter APRÈS le dernier péage sélectionné.
        Utilise les vraies motorway_junctions pour trouver la sortie optimale.
        
        Args:
            last_toll: Dernier péage sélectionné
            end_coords: Coordonnées d'arrivée
            all_tolls: Tous les péages sur la route (pour détection des péages à éviter)
            route_coords: Coordonnées de la route de base
            
        Returns:
            Dict: Segment de route
        """
        # Vérifier s'il y a des péages à éviter APRÈS le dernier péage sélectionné
        tolls_after = self.toll_positioning.get_tolls_after(last_toll, all_tolls)
        
        if tolls_after and self.junction_analyzer and route_coords:
            # Utiliser l'analyzer pour trouver la vraie sortie APRÈS le péage utilisé et AVANT les péages à éviter
            exit_junction = self.junction_analyzer.find_exit_after_toll(
                route_coords, last_toll, tolls_after
            )
            
            # Vérifier si le péage est déjà une sortie (exit_junction == None signifie péage déjà sortie)
            if hasattr(last_toll, 'is_exit') and last_toll.is_exit and exit_junction is None:
                # Le péage est déjà une sortie, aller directement à la destination sans éviter péages
                segment_type = 'avoid_tolls'
                start_coords = last_toll.osm_coordinates
                description = f"{last_toll.effective_name} vers arrivée (déjà une sortie)"
                print(f"   📍 Dernier segment : {last_toll.effective_name} → Arrivée (péage déjà sortie, évite {len(tolls_after)} péages)")
            elif exit_junction:
                # Utiliser la sortie du péage sélectionné et router vers la sortie optimale
                exit_coords = self.entrance_exit_finder.find_exit_coordinates(last_toll)
                segment_type = 'avoid_tolls'
                start_coords = exit_coords
                description = f"Sortie {last_toll.effective_name} vers arrivée"
                print(f"   📍 Dernier segment : Sortie {last_toll.effective_name} → Arrivée (évite {len(tolls_after)} péages: {[t.effective_name for t in tolls_after]})")
                print(f"       🎯 Coordonnées : {start_coords} → {end_coords}")
                print(f"       💡 Sortie optimale trouvée : {exit_junction['name']} à {exit_junction['link_coordinates']}")
            else:
                # Fallback vers la méthode classique
                exit_coords = self.entrance_exit_finder.find_exit_coordinates(last_toll)
                segment_type = 'avoid_tolls'
                start_coords = exit_coords
                description = f"Sortie {last_toll.effective_name} vers arrivée"
                print(f"   📍 Dernier segment : Sortie {last_toll.effective_name} → Arrivée (évite {len(tolls_after)} péages: {[t.effective_name for t in tolls_after]} - fallback)")
        elif tolls_after:
            # Il faut éviter les péages suivants : utiliser la sortie du péage et route sans péages
            exit_coords = self.entrance_exit_finder.find_exit_coordinates(last_toll)
            segment_type = 'avoid_tolls'
            start_coords = exit_coords
            description = f"Sortie {last_toll.effective_name} vers arrivée"
            print(f"   📍 Dernier segment : Sortie {last_toll.effective_name} → Arrivée (évite {len(tolls_after)} péages: {[t.effective_name for t in tolls_after]})")
        else:
            # Route normale du péage vers l'arrivée
            segment_type = 'normal'
            start_coords = last_toll.osm_coordinates
            description = f"{last_toll.effective_name} vers arrivée"
            print(f"   📍 Dernier segment : {last_toll.effective_name} → Arrivée (route normale)")
        
        return {
            'segment_type': segment_type,
            'start': start_coords,
            'end': end_coords,
            'description': description
        }
    
    def build_toll_to_exit_segment(
        self, 
        toll: MatchedToll, 
        all_tolls: List[MatchedToll],
        route_coords: List[List[float]] = None
    ) -> Dict:
        """
        Construit le segment péage → sortie optimale.
        
        Args:
            toll: Péage utilisé
            all_tolls: Tous les péages sur la route
            route_coords: Coordonnées de la route de base
            
        Returns:
            Dict: Segment de route
        """
        tolls_after = self.toll_positioning.get_tolls_after(toll, all_tolls)
        
        if self.junction_analyzer and route_coords:
            # Trouver la sortie optimale après le péage et avant les péages à éviter
            exit_junction = self.junction_analyzer.find_exit_after_toll(
                route_coords, toll, tolls_after
            )
            
            if exit_junction:
                # Segment du péage vers la sortie optimale (dans le bon sens)
                start_coords = toll.osm_coordinates
                end_coords = exit_junction['link_coordinates']
                
                print(f"   📍 Segment péage → sortie : {toll.effective_name} → {exit_junction['name']}")
                print(f"       🎯 Coordonnées : {start_coords} → {end_coords}")
                
                return {
                    'segment_type': 'normal',  # Route normale jusqu'à la sortie
                    'start': start_coords,
                    'end': end_coords,
                    'description': f"{toll.effective_name} vers sortie {exit_junction['name']}",
                    'exit_junction': exit_junction
                }
        
        # Fallback : utiliser la sortie calculée classiquement
        exit_coords = self.entrance_exit_finder.find_exit_coordinates(toll)
        print(f"   📍 Segment péage → sortie : {toll.effective_name} → sortie (fallback)")
        
        return {
            'segment_type': 'normal',
            'start': toll.osm_coordinates,
            'end': exit_coords,
            'description': f"{toll.effective_name} vers sortie"
        }
    
    def build_exit_to_end_segment(
        self, 
        toll: MatchedToll, 
        end_coords: List[float],
        tolls_to_avoid: List[MatchedToll]
    ) -> Dict:
        """
        Construit le segment sortie → arrivée en évitant les péages.
        
        Args:
            toll: Péage utilisé (pour obtenir la sortie)
            end_coords: Coordonnées d'arrivée
            tolls_to_avoid: Péages à éviter
            
        Returns:
            Dict: Segment de route
        """
        # Utiliser la sortie trouvée dans le segment précédent ou calculer
        exit_coords = self.entrance_exit_finder.find_exit_coordinates(toll)
        
        print(f"   📍 Segment sortie → arrivée : Sortie → Arrivée (évite {len(tolls_to_avoid)} péages)")
        print(f"       🎯 Coordonnées : {exit_coords} → {end_coords}")
        
        return {
            'segment_type': 'avoid_tolls',  # Route sans péages
            'start': exit_coords,
            'end': end_coords,
            'description': f"Sortie vers arrivée (évite péages)"
        }
