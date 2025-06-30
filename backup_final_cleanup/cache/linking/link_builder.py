"""
Link Builder
-----------

Builds complete motorway links from individual segments.
"""

import uuid
from typing import List, Dict
from dataclasses import dataclass

from ..models.motorway_link import MotorwayLink
from ..models.complete_motorway_link import CompleteMotorwayLink
from ..models.link_types import LinkType
from ..utils.geographic_utils import calculate_distance


@dataclass
class LinkingResult:
    """Résultat de la liaison des segments."""
    complete_entry_links: List[CompleteMotorwayLink]
    complete_exit_links: List[CompleteMotorwayLink]
    unlinked_indeterminate: List[MotorwayLink]
    
    def get_all_complete_links(self) -> List[CompleteMotorwayLink]:
        """Retourne tous les liens complets."""
        return self.complete_entry_links + self.complete_exit_links
    
    def get_stats(self) -> Dict[str, int]:
        """Retourne les statistiques de liaison."""
        return {
            'complete_entry_links': len(self.complete_entry_links),
            'complete_exit_links': len(self.complete_exit_links),
            'unlinked_indeterminate': len(self.unlinked_indeterminate),
            'total_complete_links': len(self.get_all_complete_links())
        }


class LinkBuilder:
    """Constructeur de liens complets à partir des segments individuels."""
    
    def __init__(self, max_distance_m: float = 2.0):
        """
        Initialise le constructeur de liens.
        
        Args:
            max_distance_m: Distance maximale pour lier deux segments (mètres)
        """
        self.max_distance_m = max_distance_m
    
    def build_complete_links(
        self, 
        entry_links: List[MotorwayLink],
        exit_links: List[MotorwayLink], 
        indeterminate_links: List[MotorwayLink]
    ) -> LinkingResult:
        """
        Construit les liens complets en associant les segments.
        
        Args:
            entry_links: Segments d'entrée
            exit_links: Segments de sortie
            indeterminate_links: Segments indéterminés
            
        Returns:
            LinkingResult: Résultat de la liaison
        """
        print("🔗 Construction des liens complets...")
        
        # 1. Créer les liens complets pour les entrées
        complete_entries = self._build_complete_links_for_type(
            entry_links, indeterminate_links, LinkType.ENTRY
        )
        
        # 2. Créer les liens complets pour les sorties
        complete_exits = self._build_complete_links_for_type(
            exit_links, indeterminate_links, LinkType.EXIT
        )
        
        # 3. Segments indéterminés non utilisés
        used_indeterminate_ids = set()
        for complete_link in complete_entries + complete_exits:
            for segment in complete_link.segments:
                if segment.link_type == LinkType.INDETERMINATE:
                    used_indeterminate_ids.add(segment.way_id)
        
        unlinked_indeterminate = [
            link for link in indeterminate_links 
            if link.way_id not in used_indeterminate_ids
        ]
        
        result = LinkingResult(
            complete_entry_links=complete_entries,
            complete_exit_links=complete_exits,
            unlinked_indeterminate=unlinked_indeterminate
        )
        
        self._print_linking_summary(result)
        return result
    
    def _build_complete_links_for_type(
        self, 
        typed_links: List[MotorwayLink],
        indeterminate_links: List[MotorwayLink],
        link_type: LinkType
    ) -> List[CompleteMotorwayLink]:
        """Construit les liens complets pour un type donné."""
        complete_links = []
        used_indeterminate_ids = set()
        
        for typed_link in typed_links:
            # Créer un lien complet avec le segment typé comme base
            complete_link = CompleteMotorwayLink(
                link_id=f"{link_type.value}_{str(uuid.uuid4())[:8]}",
                link_type=link_type,
                segments=[typed_link],
                destination=typed_link.destination
            )
            
            # Chercher des segments indéterminés à associer
            connected_segments = self._find_connected_segments(
                typed_link, indeterminate_links, used_indeterminate_ids
            )
            
            # Ajouter les segments connectés
            for segment in connected_segments:
                complete_link.add_segment(segment)
                used_indeterminate_ids.add(segment.way_id)
            
            complete_links.append(complete_link)
        
        return complete_links
    
    def _find_connected_segments(
        self,
        base_segment: MotorwayLink,
        candidate_segments: List[MotorwayLink],
        used_ids: set
    ) -> List[MotorwayLink]:
        """Trouve les segments indéterminés connectés à un segment de base."""
        connected = []
        
        # Points de connexion possibles du segment de base
        base_start = base_segment.get_start_point()
        base_end = base_segment.get_end_point()
        
        for candidate in candidate_segments:
            if candidate.way_id in used_ids:
                continue
            
            candidate_start = candidate.get_start_point()
            candidate_end = candidate.get_end_point()
            
            # Vérifier si les segments sont connectés (distance < seuil en mètres)
            from ..utils.geographic_utils import calculate_distance
            distances = [
                calculate_distance(base_start, candidate_start) * 1000,  # Convertir km → m
                calculate_distance(base_start, candidate_end) * 1000,
                calculate_distance(base_end, candidate_start) * 1000,
                calculate_distance(base_end, candidate_end) * 1000
            ]
            
            min_distance = min(distances)
            if min_distance <= self.max_distance_m:
                connected.append(candidate)
        
        return connected
    
    def _print_linking_summary(self, result: LinkingResult):
        """Affiche un résumé de la liaison."""
        stats = result.get_stats()
        print(f"📊 Résumé de la liaison:")
        print(f"   • Liens d'entrée complets: {stats['complete_entry_links']}")
        print(f"   • Liens de sortie complets: {stats['complete_exit_links']}")
        print(f"   • Segments indéterminés non liés: {stats['unlinked_indeterminate']}")
        print(f"   • Total liens complets: {stats['total_complete_links']}")
        print("✅ Construction des liens terminée!\n")
