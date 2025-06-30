"""
Segment Chain Builder
--------------------

Builds chains of connected indeterminate motorway segments.
"""

from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass

from ..models.motorway_link import MotorwayLink
from ..models.link_types import LinkType
from .coordinate_matcher import SegmentConnectionAnalyzer


@dataclass
class SegmentChain:
    """Chaîne de segments connectés."""
    chain_id: str
    segments: List[MotorwayLink]
    
    def get_start_point(self) -> List[float]:
        """Retourne le point de début de la chaîne."""
        return self.segments[0].get_start_point() if self.segments else [0.0, 0.0]
    
    def get_end_point(self) -> List[float]:
        """Retourne le point de fin de la chaîne."""
        return self.segments[-1].get_end_point() if self.segments else [0.0, 0.0]
    
    def add_segment_at_end(self, segment: MotorwayLink):
        """Ajoute un segment à la fin de la chaîne."""
        self.segments.append(segment)
    
    def add_segment_at_start(self, segment: MotorwayLink):
        """Ajoute un segment au début de la chaîne."""
        self.segments.insert(0, segment)
    
    def get_segment_count(self) -> int:
        """Retourne le nombre de segments dans la chaîne."""
        return len(self.segments)
    
    def get_all_way_ids(self) -> Set[str]:
        """Retourne tous les way_id des segments de la chaîne."""
        return {segment.way_id for segment in self.segments}


@dataclass
class ChainBuildingResult:
    """Résultat de la construction des chaînes."""
    chains: List[SegmentChain]
    orphaned_segments: List[MotorwayLink]
    
    def get_stats(self) -> Dict[str, int]:
        """Retourne les statistiques de chaînage."""
        total_chained = sum(chain.get_segment_count() for chain in self.chains)
        return {
            'chains_count': len(self.chains),
            'total_chained_segments': total_chained,
            'orphaned_segments': len(self.orphaned_segments),
            'total_segments': total_chained + len(self.orphaned_segments)
        }


class SegmentChainBuilder:
    """Constructeur de chaînes de segments indéterminés."""
    
    def __init__(self, max_distance_m: float = 2.0):
        """
        Initialise le constructeur de chaînes.
        
        Args:
            max_distance_m: Distance maximale pour lier deux segments
        """
        self.analyzer = SegmentConnectionAnalyzer(max_distance_m)
    
    def build_chains(self, indeterminate_segments: List[MotorwayLink]) -> ChainBuildingResult:
        """
        Construit des chaînes à partir des segments indéterminés.
        
        Args:
            indeterminate_segments: Segments indéterminés à chaîner
            
        Returns:
            ChainBuildingResult: Résultat du chaînage
        """
        print(f"🔗 Construction des chaînes à partir de {len(indeterminate_segments)} segments indéterminés...")
        
        # Créer une copie de travail
        available_segments = indeterminate_segments.copy()
        chains = []
        iteration = 0
        
        # Processus itératif jusqu'à convergence
        while available_segments:
            iteration += 1
            print(f"   Itération {iteration}: {len(available_segments)} segments restants")
            
            initial_count = len(available_segments)
            
            # Essayer de créer de nouvelles chaînes et d'étendre les existantes
            available_segments, new_chains = self._process_iteration(available_segments, chains)
            chains.extend(new_chains)
            
            # Si aucun segment n'a été traité, arrêter
            if len(available_segments) == initial_count:
                print(f"   Convergence atteinte: aucune nouvelle liaison possible")
                break
        
        result = ChainBuildingResult(
            chains=chains,
            orphaned_segments=available_segments
        )
        
        self._print_chain_statistics(result)
        return result
    
    def _process_iteration(
        self, 
        available_segments: List[MotorwayLink], 
        existing_chains: List[SegmentChain]
    ) -> Tuple[List[MotorwayLink], List[SegmentChain]]:
        """
        Traite une itération de chaînage.
        
        Returns:
            Tuple[segments_restants, nouvelles_chaînes]
        """
        used_segment_ids = set()
        new_chains = []
        
        # 1. Étendre les chaînes existantes
        for chain in existing_chains:
            extended_ids = self._extend_chain(chain, available_segments)
            used_segment_ids.update(extended_ids)
        
        # 2. Créer de nouvelles chaînes avec les segments restants
        remaining_segments = [
            seg for seg in available_segments 
            if seg.way_id not in used_segment_ids
        ]
        
        for segment in remaining_segments:
            if segment.way_id in used_segment_ids:
                continue
            
            # Chercher des segments connectés pour former une nouvelle chaîne
            chain_segments, used_ids = self._build_chain_from_segment(segment, remaining_segments)
            
            if len(chain_segments) > 0:  # Au moins le segment de base
                chain = SegmentChain(
                    chain_id=f"chain_{len(existing_chains) + len(new_chains) + 1}",
                    segments=chain_segments
                )
                new_chains.append(chain)
                used_segment_ids.update(used_ids)
        
        # Segments non utilisés pour la prochaine itération
        remaining_segments = [
            seg for seg in available_segments 
            if seg.way_id not in used_segment_ids
        ]
        
        return remaining_segments, new_chains
    
    def _extend_chain(self, chain: SegmentChain, available_segments: List[MotorwayLink]) -> Set[str]:
        """
        Étend une chaîne existante avec de nouveaux segments.
        
        Returns:
            Set[str]: IDs des segments utilisés pour l'extension
        """
        used_ids = set()
        extended = True
        
        while extended:
            extended = False
            
            # Essayer d'étendre à la fin de la chaîne
            for segment in available_segments:
                if segment.way_id in used_ids or segment.way_id in chain.get_all_way_ids():
                    continue
                
                # Test si le segment peut se connecter à la fin de la chaîne
                can_connect, connection_type, _ = self.analyzer.find_connection_type(
                    chain.get_end_point(), chain.get_end_point(),
                    segment.get_start_point(), segment.get_end_point()
                )
                
                if can_connect and connection_type == "end_to_start":
                    chain.add_segment_at_end(segment)
                    used_ids.add(segment.way_id)
                    extended = True
                    break
            
            # Essayer d'étendre au début de la chaîne
            if not extended:
                for segment in available_segments:
                    if segment.way_id in used_ids or segment.way_id in chain.get_all_way_ids():
                        continue
                    
                    # Test si le segment peut se connecter au début de la chaîne
                    can_connect, connection_type, _ = self.analyzer.find_connection_type(
                        segment.get_start_point(), segment.get_end_point(),
                        chain.get_start_point(), chain.get_start_point()
                    )
                    
                    if can_connect and connection_type == "end_to_start":
                        chain.add_segment_at_start(segment)
                        used_ids.add(segment.way_id)
                        extended = True
                        break
        
        return used_ids
    
    def _build_chain_from_segment(
        self, 
        base_segment: MotorwayLink, 
        available_segments: List[MotorwayLink]
    ) -> Tuple[List[MotorwayLink], Set[str]]:
        """
        Construit une chaîne à partir d'un segment de base.
        
        Returns:
            Tuple[segments_de_la_chaîne, ids_utilisés]
        """
        chain_segments = [base_segment]
        used_ids = {base_segment.way_id}
        
        # Étendre la chaîne dans les deux directions
        extended = True
        while extended:
            extended = False
            
            # Chercher des connexions
            for segment in available_segments:
                if segment.way_id in used_ids:
                    continue
                
                # Test connexion avec le début de la chaîne
                first_seg = chain_segments[0]
                can_connect, connection_type, _ = self.analyzer.find_connection_type(
                    segment.get_start_point(), segment.get_end_point(),
                    first_seg.get_start_point(), first_seg.get_end_point()
                )
                
                if can_connect and connection_type == "end_to_start":
                    chain_segments.insert(0, segment)
                    used_ids.add(segment.way_id)
                    extended = True
                    break
                
                # Test connexion avec la fin de la chaîne
                last_seg = chain_segments[-1]
                can_connect, connection_type, _ = self.analyzer.find_connection_type(
                    last_seg.get_start_point(), last_seg.get_end_point(),
                    segment.get_start_point(), segment.get_end_point()
                )
                
                if can_connect and connection_type == "end_to_start":
                    chain_segments.append(segment)
                    used_ids.add(segment.way_id)
                    extended = True
                    break
        
        return chain_segments, used_ids
    
    def _print_chain_statistics(self, result: ChainBuildingResult):
        """Affiche les statistiques de chaînage."""
        stats = result.get_stats()
        print(f"📊 Résultat du chaînage:")
        print(f"   • Chaînes créées: {stats['chains_count']}")
        print(f"   • Segments chaînés: {stats['total_chained_segments']}")
        print(f"   • Segments orphelins: {stats['orphaned_segments']}")
        print(f"   • Total segments: {stats['total_segments']}")
        
        if result.chains:
            chain_sizes = [chain.get_segment_count() for chain in result.chains]
            avg_size = sum(chain_sizes) / len(chain_sizes)
            print(f"   • Taille moyenne des chaînes: {avg_size:.1f} segments")
            print(f"   • Plus grande chaîne: {max(chain_sizes)} segments")
        
        print("✅ Construction des chaînes terminée!\n")
