"""
toll_segment_builder.py
-----------------------

Module pour construire les segments de route intelligents.
Responsabilité : créer les segments en évitant les péages non-désirés.
"""

from typing import List, Dict, Tuple, Optional
from .toll_matcher import MatchedToll
from .toll_entrance_exit_finder import TollEntranceExitFinder
from .motorway_junction_analyzer import MotorwayJunctionAnalyzer


class TollSegmentBuilder:
    """
    Construit les segments de route pour éviter les péages non-désirés.
    """
    
    def __init__(self, ors_service):
        """
        Initialise avec le service ORS.
        
        Args:
            ors_service: Service ORS pour les calculs de routes
        """        
        self.ors = ors_service
        self.entrance_exit_finder = TollEntranceExitFinder(ors_service)
        self.junction_analyzer = None  # Sera initialisé avec le parser OSM
    
    def build_intelligent_segments(
        self, 
        start_coords: List[float], 
        end_coords: List[float],
        all_tolls_on_route: List[MatchedToll], 
        selected_tolls: List[MatchedToll],
        osm_parser = None,
        route_coords: List[List[float]] = None
    ) -> List[Dict]:
        """
        Construit les segments intelligents avec la nouvelle logique granulaire.
        
        Règles :
        - Segment vers péage seulement si nécessaire
        - Segment péage → sortie SEULEMENT si péages à éviter après
        - Segment sortie → entrée pour éviter des péages
        - Segment entrée → péage si nécessaire
        
        Args:
            start_coords: Coordonnées de départ
            end_coords: Coordonnées d'arrivée
            all_tolls_on_route: Tous les péages sur la route directe
            selected_tolls: Péages que l'on veut utiliser
            osm_parser: Parser OSM pour les junctions
            route_coords: Coordonnées de la route de base
            
        Returns:
            List[Dict]: Segments de route à calculer
        """
        print(f"🧩 Construction granulaire pour {len(selected_tolls)} péages sélectionnés...")
        
        # Initialiser l'analyzer de junctions avec les données OSM
        if osm_parser and route_coords:
            self.junction_analyzer = MotorwayJunctionAnalyzer(osm_parser)
            print("🔍 Analyse des motorway_junctions sur la route...")
        
        segments = []
        
        # Cas spécial : aucun péage sélectionné
        if not selected_tolls:
            return []
          # Construire les segments selon la nouvelle logique
        segments = self._build_granular_segments(
            start_coords, end_coords, all_tolls_on_route, selected_tolls, route_coords
        )
        
        return segments
    
    def _build_granular_segments(
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
                tolls_before = self._get_tolls_before(current_toll, all_tolls)
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
                tolls_after = self._get_tolls_after(current_toll, all_tolls)
                if tolls_after:
                    # Éviter les péages après : Péage → Sortie, puis Sortie → Arrivée
                    exit_coords = self._find_optimal_exit_after_toll(current_toll, tolls_after, route_coords)
                    
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
                tolls_between = self._get_tolls_between(current_toll, next_toll, all_tolls)
                
                if tolls_between:
                    # Il y a des péages à éviter : Péage → Sortie, puis Sortie → Entrée suivant
                    exit_coords = self._find_optimal_exit_after_toll(current_toll, tolls_between, route_coords)
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
    
    def _find_optimal_exit_after_toll(
        self,
        toll: MatchedToll,
        tolls_to_avoid: List[MatchedToll],
        route_coords: List[List[float]]
    ) -> List[float]:
        """
        Trouve la sortie optimale après un péage pour éviter d'autres péages.
        """
        if self.junction_analyzer and route_coords:
            exit_junction = self.junction_analyzer.find_exit_after_toll(
                route_coords, toll, tolls_to_avoid
            )
            if exit_junction and 'link_coordinates' in exit_junction:
                print(f"       💡 Sortie optimale trouvée : {exit_junction['name']} à {exit_junction['link_coordinates']}")
                return exit_junction['link_coordinates']
        
        # Fallback vers la méthode classique
        return self.entrance_exit_finder.find_exit_coordinates(toll)
    
    def _build_first_segment(
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
        """        # Vérifier s'il y a des péages à éviter avant le premier péage
        tolls_before = self._get_tolls_before(first_toll, all_tolls)
        
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
            'type': segment_type,
            'start': start_coords,
            'end': end_coords,
            'description': f"Départ vers {first_toll.effective_name}"
        }
    
    def _build_intermediate_segment(
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
        tolls_between = self._get_tolls_between(previous_toll, current_toll, all_tolls)
        
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
        
        return {            'type': segment_type,            'start': start_coords,
            'end': end_coords,
            'description': f"{previous_toll.effective_name} vers {current_toll.effective_name}"
        }
    
    def _build_last_segment(
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
        tolls_after = self._get_tolls_after(last_toll, all_tolls)
        
        if tolls_after and self.junction_analyzer and route_coords:
            # Utiliser l'analyzer pour trouver la vraie sortie APRÈS le péage utilisé et AVANT les péages à éviter
            exit_junction = self.junction_analyzer.find_exit_after_toll(
                route_coords, last_toll, tolls_after
            )
            
            if exit_junction:
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
            'type': segment_type,
            'start': start_coords,
            'end': end_coords,
            'description': description
        }
    
    def _build_toll_to_exit_segment(
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
        tolls_after = self._get_tolls_after(toll, all_tolls)
        
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
                    'type': 'normal',  # Route normale jusqu'à la sortie
                    'start': start_coords,
                    'end': end_coords,
                    'description': f"{toll.effective_name} vers sortie {exit_junction['name']}",
                    'exit_junction': exit_junction
                }
        
        # Fallback : utiliser la sortie calculée classiquement
        exit_coords = self.entrance_exit_finder.find_exit_coordinates(toll)
        print(f"   📍 Segment péage → sortie : {toll.effective_name} → sortie (fallback)")
        
        return {
            'type': 'normal',
            'start': toll.osm_coordinates,
            'end': exit_coords,
            'description': f"{toll.effective_name} vers sortie"
        }
    
    def _build_exit_to_end_segment(
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
            'type': 'avoid_tolls',  # Route sans péages
            'start': exit_coords,
            'end': end_coords,
            'description': f"Sortie vers arrivée (évite péages)"
        }

    def _get_tolls_before(self, target_toll: MatchedToll, all_tolls: List[MatchedToll]) -> List[MatchedToll]:
        """
        Récupère les péages qui viennent avant un péage cible sur la route.
        
        Args:
            target_toll: Péage cible
            all_tolls: Tous les péages sur la route (ordonnés)
            
        Returns:
            List[MatchedToll]: Péages avant le péage cible
        """
        try:
            target_index = all_tolls.index(target_toll)
            return all_tolls[:target_index]
        except ValueError:
            return []
    
    def _get_tolls_between(
        self, 
        toll1: MatchedToll, 
        toll2: MatchedToll, 
        all_tolls: List[MatchedToll]
    ) -> List[MatchedToll]:
        """
        Récupère les péages entre deux péages sur la route.
        
        Args:
            toll1: Premier péage
            toll2: Deuxième péage
            all_tolls: Tous les péages sur la route (ordonnés)
            
        Returns:
            List[MatchedToll]: Péages entre toll1 et toll2
        """
        try:
            index1 = all_tolls.index(toll1)
            index2 = all_tolls.index(toll2)
            
            if index1 < index2:
                return all_tolls[index1 + 1:index2]
            else:
                return all_tolls[index2 + 1:index1]
        except ValueError:
            return []
    
    def _get_tolls_after(self, target_toll: MatchedToll, all_tolls: List[MatchedToll]) -> List[MatchedToll]:
        """
        Récupère les péages qui viennent APRÈS un péage cible sur la route.
        
        Args:
            target_toll: Péage cible
            all_tolls: Tous les péages sur la route (ordonnés)
            
        Returns:
            List[MatchedToll]: Péages après le péage cible
        """
        try:
            target_index = all_tolls.index(target_toll)
            return all_tolls[target_index + 1:]
        except ValueError:
            return []
