"""
junction_linker.py
------------------

Module pour associer les motorway_junctions avec leurs chaînes de motorway_links.

Responsabilité : orchestrer le processus de liaison des éléments OSM.
"""

from typing import List
from src.services.toll.new_segmentation.osm_data_parser import MotorwayJunction, MotorwayLink
from src.services.toll.new_segmentation.linking.link_finder import LinkFinder


class JunctionLinker:
    """
    Classe pour lier les junctions avec leurs chaînes de motorway_links.
    """
    
    def __init__(self):
        """Initialise le linker."""
        self.link_finder = LinkFinder(max_distance_m=2.0)
    
    def link_all_junctions(
        self, 
        junctions: List[MotorwayJunction], 
        motorway_links: List[MotorwayLink]
    ) -> None:
        """
        Lie toutes les junctions avec leurs chaînes de motorway_links.
        
        Args:
            junctions: Liste des junctions à traiter
            motorway_links: Liste des motorway_links disponibles (sera modifiée)
        """
        # Copie de travail des liens disponibles
        available_links = motorway_links.copy()
        
        print(f"🔗 Début du linking : {len(junctions)} junctions, {len(available_links)} links")
        
        for junction in junctions:
            self._link_single_junction(junction, available_links)
        
        print(f"✅ Linking terminé : {len(available_links)} links non utilisés")
        
        # Afficher les statistiques
        self._print_linking_statistics(junctions)
    
    def _link_single_junction(
        self, 
        junction: MotorwayJunction, 
        available_links: List[MotorwayLink]
    ) -> None:
        """
        Lie une seule junction avec sa chaîne de motorway_links.
        
        Args:
            junction: Junction à traiter
            available_links: Liste des liens disponibles (sera modifiée)
        """
        # Trouver le premier lien associé à cette junction
        first_link = self.link_finder.find_link_near_junction(junction, available_links)
        
        if first_link is None:
            # Pas de lien trouvé pour cette junction
            junction.linked_motorway_links = []
            return
        
        # Construire la chaîne complète de liens
        link_chain = self.link_finder.build_link_chain(first_link, available_links)
        
        # Assigner la chaîne à la junction
        junction.linked_motorway_links = link_chain
        
        # Lier les éléments entre eux dans la chaîne
        for i in range(len(link_chain) - 1):
            link_chain[i].next_link = link_chain[i + 1]
        
        # Le dernier lien n'a pas de suivant
        if link_chain:
            link_chain[-1].next_link = None
    
    def _print_linking_statistics(self, junctions: List[MotorwayJunction]) -> None:
        """
        Affiche les statistiques du linking.
        
        Args:
            junctions: Liste des junctions liées
        """
        total_links = 0
        junctions_with_links = 0
        
        for junction in junctions:
            if hasattr(junction, 'linked_motorway_links') and junction.linked_motorway_links:
                junctions_with_links += 1
                total_links += len(junction.linked_motorway_links)
        
        print(f"📊 Statistiques de linking :")
        print(f"   - Junctions avec des liens : {junctions_with_links}/{len(junctions)}")
        print(f"   - Total de links liés : {total_links}")
    
    def find_junction_by_id(self, junctions: List[MotorwayJunction], target_id: str) -> MotorwayJunction:
        """
        Trouve une junction par son ID.
        
        Args:
            junctions: Liste des junctions
            target_id: ID à rechercher
            
        Returns:
            MotorwayJunction: Junction trouvée ou None
        """
        for junction in junctions:
            if junction.node_id == target_id or junction.node_id.endswith(f"/{target_id}"):
                return junction
        return None
