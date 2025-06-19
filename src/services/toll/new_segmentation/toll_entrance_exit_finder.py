"""
toll_entrance_exit_finder.py
-----------------------------

Module pour trouver les entrées et sorties des péages.
Responsabilité : localiser les points d'entrée et de sortie autour des péages.
"""

from typing import List, Dict, Tuple, Optional
from .toll_matcher import MatchedToll


class TollEntranceExitFinder:
    """
    Trouve les entrées et sorties des péages pour la segmentation intelligente.
    """
    
    def __init__(self, ors_service):
        """
        Initialise avec le service ORS.
        
        Args:
            ors_service: Service ORS pour les calculs de routes
        """
        self.ors = ors_service
    
    def find_entrance_coordinates(self, toll: MatchedToll, buffer_km: float = 2.0) -> List[float]:
        """
        Trouve les coordonnées d'entrée d'un péage.
        
        Args:
            toll: Péage pour lequel trouver l'entrée
            buffer_km: Distance de recherche en km
            
        Returns:
            List[float]: [longitude, latitude] de l'entrée
        """
        # Pour l'instant, utiliser les coordonnées du péage avec un léger décalage
        # Dans une implémentation plus avancée, on pourrait chercher les vraies entrées
        toll_coords = toll.osm_coordinates
        
        # Décalage approximatif vers l'entrée (buffer en arrière)
        entrance_coords = [
            toll_coords[0] - 0.01,  # Légèrement à l'ouest
            toll_coords[1]
        ]
        
        print(f"   🚪 Entrée estimée pour {toll.effective_name} : {entrance_coords}")
        return entrance_coords
    
    def find_exit_coordinates(self, toll: MatchedToll, buffer_km: float = 2.0) -> List[float]:
        """
        Trouve les coordonnées de sortie d'un péage.
        
        Args:
            toll: Péage pour lequel trouver la sortie
            buffer_km: Distance de recherche en km
            
        Returns:
            List[float]: [longitude, latitude] de la sortie
        """
        # Pour l'instant, utiliser les coordonnées du péage avec un léger décalage
        toll_coords = toll.osm_coordinates
        
        # Décalage approximatif vers la sortie (buffer en avant)
        exit_coords = [
            toll_coords[0] + 0.01,  # Légèrement à l'est
            toll_coords[1]
        ]
        
        print(f"   🚪 Sortie estimée pour {toll.effective_name} : {exit_coords}")
        return exit_coords
    
    def get_toll_boundaries(self, toll: MatchedToll) -> Dict[str, List[float]]:
        """
        Récupère les coordonnées d'entrée et de sortie d'un péage.
        
        Args:
            toll: Péage à analyser
            
        Returns:
            Dict: {'entrance': [lon, lat], 'exit': [lon, lat]}
        """
        return {
            'entrance': self.find_entrance_coordinates(toll),
            'exit': self.find_exit_coordinates(toll)
        }
