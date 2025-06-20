"""
toll_positioning.py
------------------

Module pour les utilitaires de positionnement des péages.
Responsabilité : gérer les relations spatiales entre péages (avant, après, entre).
"""

from typing import List
from ..toll_matcher import MatchedToll


class TollPositioning:
    """
    Utilitaires pour déterminer les positions relatives des péages sur une route.
    """
    
    @staticmethod
    def get_tolls_before(target_toll: MatchedToll, all_tolls: List[MatchedToll]) -> List[MatchedToll]:
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
    
    @staticmethod
    def get_tolls_between(
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
    
    @staticmethod
    def get_tolls_after(target_toll: MatchedToll, all_tolls: List[MatchedToll]) -> List[MatchedToll]:
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
