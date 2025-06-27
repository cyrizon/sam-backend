"""
strategic_entrance_finder.py
----------------------------

Module pour trouver des entrées d'autoroute stratégiques.
Responsabilité : identifier les bonnes entrées d'autoroute pour éviter certains péages
tout en atteignant d'autres péages de manière logique.
"""

from typing import List, Optional
from src.cache.models.matched_toll import MatchedToll
from .highway_entrance_analyzer import HighwayEntranceAnalyzer


class StrategicEntranceFinder:
    """
    Trouve des entrées d'autoroute stratégiques pour une navigation intelligente.
    """
    def __init__(self, entrance_exit_finder, junction_analyzer=None):
        """
        Initialise le finder avec les outils nécessaires.
        
        Args:
            entrance_exit_finder: Finder pour les entrées/sorties classiques
            junction_analyzer: Analyzer pour les junctions (optionnel)
        """
        self.entrance_exit_finder = entrance_exit_finder
        self.junction_analyzer = junction_analyzer
        self.highway_analyzer = HighwayEntranceAnalyzer(entrance_exit_finder)
    
    def find_strategic_entrance_before_toll(
        self,
        target_toll: MatchedToll,
        tolls_to_avoid: List[MatchedToll],
        route_coords: List[List[float]] = None
    ) -> Optional[List[float]]:
        """
        Trouve une entrée d'autoroute stratégique située APRÈS les péages à éviter
        et AVANT le péage cible.
        
        Cette méthode évite le problème actuel où on essaie d'aller directement
        au péage cible sans péage (impossible).
        
        Args:
            target_toll: Péage qu'on veut atteindre
            tolls_to_avoid: Péages qu'on veut éviter (situés avant target_toll)            route_coords: Coordonnées de la route de base
            
        Returns:
            Optional[List[float]]: Coordonnées de l'entrée stratégique ou None
        """        
        if self.junction_analyzer and route_coords:
            print(f"       🔍 Tentative d'utilisation du junction_analyzer...")
            # Utiliser l'analyzer pour trouver une entrée intelligente
            if hasattr(self.junction_analyzer, 'find_entrance_between_tolls'):
                print(f"       ✅ Méthode find_entrance_between_tolls disponible")
                strategic_entrance = self.junction_analyzer.find_entrance_between_tolls(
                    route_coords, tolls_to_avoid, target_toll
                )
                
                if strategic_entrance:
                    entrance_coords = strategic_entrance.get('link_coordinates')
                    entrance_name = strategic_entrance.get('name', 'Entrée')
                    
                    if entrance_coords:
                        print(f"       💡 Entrée stratégique trouvée : {entrance_name} à {entrance_coords}")
                        return entrance_coords
                    else:
                        print(f"       ⚠️ Entrée trouvée mais coordonnées manquantes : {strategic_entrance}")
                else:
                    print(f"       ❌ Aucune entrée trouvée par junction_analyzer")
            else:
                print(f"       ❌ Méthode find_entrance_between_tolls non disponible")
        else:
            if not self.junction_analyzer:
                print(f"       ⚠️ junction_analyzer non initialisé")
            if not route_coords:
                print(f"       ⚠️ route_coords non fournie")
                    
        # Fallback : utiliser notre analyzer géographique intelligent
        strategic_entrance = self.highway_analyzer.find_entrance_between_tolls(
            tolls_to_avoid, target_toll
        )
        
        if strategic_entrance:
            return strategic_entrance
            
        # Dernier fallback : méthode classique
        return self._find_fallback_entrance(target_toll, tolls_to_avoid)
    
    def _find_fallback_entrance(
        self,
        target_toll: MatchedToll,
        tolls_to_avoid: List[MatchedToll]
    ) -> List[float]:
        """
        Méthode de fallback pour trouver une entrée quand l'analyzer n'est pas disponible.
        
        Pour l'instant, utilise la méthode classique mais on pourrait améliorer
        avec une logique géographique plus sophistiquée.
        
        Args:
            target_toll: Péage cible
            tolls_to_avoid: Péages à éviter
            
        Returns:
            List[float]: Coordonnées d'entrée (fallback)
        """
        # Pour l'instant, fallback vers la méthode existante
        # TODO: Implémenter une logique plus intelligente
        print(f"       ⚠️ Utilisation du fallback pour trouver l'entrée vers {target_toll.effective_name}")
        return self.entrance_exit_finder.find_entrance_coordinates(target_toll)
