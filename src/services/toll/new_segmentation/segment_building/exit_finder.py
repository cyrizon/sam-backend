"""
exit_finder.py
--------------

Module pour la recherche de sorties optimales.
Responsabilité : trouver les meilleures sorties après les péages pour éviter d'autres péages.
"""

from typing import List, Optional
from ..toll_matcher import MatchedToll


class ExitFinder:
    """
    Trouve les sorties optimales après les péages.
    """
    
    def __init__(self, entrance_exit_finder, junction_analyzer=None):
        """
        Initialise le finder avec les outils nécessaires.
        
        Args:
            entrance_exit_finder: Finder pour les entrées/sorties
            junction_analyzer: Analyzer pour les junctions (optionnel)
        """
        self.entrance_exit_finder = entrance_exit_finder
        self.junction_analyzer = junction_analyzer
    
    def find_optimal_exit_after_toll(
        self,
        toll: MatchedToll,
        tolls_to_avoid: List[MatchedToll],
        route_coords: List[List[float]]
    ) -> List[float]:
        """
        Trouve la sortie optimale après un péage pour éviter d'autres péages.
        
        Args:
            toll: Péage de référence
            tolls_to_avoid: Péages à éviter
            route_coords: Coordonnées de la route
            
        Returns:
            List[float]: Coordonnées de la sortie optimale
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
