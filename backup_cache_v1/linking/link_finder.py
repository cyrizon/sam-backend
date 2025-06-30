"""
Link Finder
-----------

Module for finding links between motorway_junctions and motorway_links.
Refactored from linking/link_finder.py with updated imports.
"""

from typing import List, Optional
from ..models.motorway_junction import MotorwayJunction
from ..models.motorway_link import MotorwayLink
from src.cache.linking.distance_calculator import is_within_distance


class LinkFinder:
    """
    Classe pour trouver les liens entre junctions et motorway_links.
    """
    
    def __init__(self, max_distance_m: float = 2.0):
        """
        Initialise le finder avec une distance maximale.
        
        Args:
            max_distance_m: Distance maximale en mètres pour considérer deux points comme liés
        """
        self.max_distance_m = max_distance_m
    
    def find_link_near_junction(
        self, 
        junction: MotorwayJunction, 
        available_links: List[MotorwayLink]
    ) -> Optional[MotorwayLink]:
        """
        Trouve la motorway_link la plus proche d'une junction.
        
        Args:
            junction: Junction à partir de laquelle chercher
            available_links: Liste des liens disponibles
            
        Returns:
            MotorwayLink: Le lien trouvé ou None
        """
        junction_coords = junction.coordinates
        
        for link in available_links:
            # Vérifier si le début du lien est proche de la junction
            start_point = link.get_start_point()
            if is_within_distance(junction_coords, start_point, self.max_distance_m):
                return link
                
        return None
    
    def find_next_link(
        self, 
        current_link: MotorwayLink, 
        available_links: List[MotorwayLink]
    ) -> Optional[MotorwayLink]:
        """
        Trouve la motorway_link suivante dans la chaîne.
        
        Args:
            current_link: Lien actuel
            available_links: Liste des liens disponibles
            
        Returns:
            MotorwayLink: Le lien suivant ou None
        """
        current_end = current_link.get_end_point()
        
        for link in available_links:
            # Éviter de se lier à soi-même
            if link.way_id == current_link.way_id:
                continue
                
            # Vérifier si le début du lien candidat est proche de la fin du lien actuel
            candidate_start = link.get_start_point()
            if is_within_distance(current_end, candidate_start, self.max_distance_m):
                return link
                
        return None
    
    def build_link_chain(
        self, 
        first_link: MotorwayLink, 
        available_links: List[MotorwayLink]
    ) -> List[MotorwayLink]:
        """
        Construit la chaîne complète de motorway_links à partir du premier lien.
        
        Args:
            first_link: Premier lien de la chaîne
            available_links: Liste des liens disponibles (sera modifiée)
            
        Returns:
            List[MotorwayLink]: Chaîne complète des liens
        """
        chain = [first_link]
        current_link = first_link
        
        # Retirer le premier lien de la liste disponible
        if first_link in available_links:
            available_links.remove(first_link)
        
        # Construire la chaîne
        while True:
            next_link = self.find_next_link(current_link, available_links)
            if next_link is None:
                break
                
            chain.append(next_link)
            available_links.remove(next_link)
            current_link = next_link
            
        return chain
