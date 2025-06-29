"""
Simple Chain Builder
-------------------

Constructeur de chaînes simplifié basé uniquement sur la correspondance exacte des coordonnées.
"""

from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass

from ..models.motorway_link import MotorwayLink
from ..models.link_types import LinkType
from .coordinate_matcher import are_coordinates_equal


@dataclass
class SimpleChain:
    """Chaîne simple de segments connectés."""
    chain_id: str
    segments: List[MotorwayLink]
    
    def get_start_point(self) -> List[float]:
        """Retourne le point de début de la chaîne."""
        return self.segments[0].get_start_point() if self.segments else [0.0, 0.0]
    
    def get_end_point(self) -> List[float]:
        """Retourne le point de fin de la chaîne."""
        return self.segments[-1].get_end_point() if self.segments else [0.0, 0.0]
    
    def get_segment_count(self) -> int:
        """Retourne le nombre de segments dans la chaîne."""
        return len(self.segments)
    
    def get_all_way_ids(self) -> Set[str]:
        """Retourne tous les way_id des segments de la chaîne."""
        return {segment.way_id for segment in self.segments}


@dataclass
class SimpleChainResult:
    """Résultat de la construction des chaînes."""
    chains: List[SimpleChain]
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


class SimpleChainBuilder:
    """Constructeur de chaînes simplifié."""
    
    def __init__(self):
        """Initialise le constructeur."""
        pass
    
    def build_chains(self, indeterminate_segments: List[MotorwayLink]) -> SimpleChainResult:
        """
        Construit des chaînes à partir des segments indéterminés.
        
        Args:
            indeterminate_segments: Segments indéterminés à chaîner
            
        Returns:
            SimpleChainResult: Résultat du chaînage
        """
        print(f"🔗 Construction simple des chaînes à partir de {len(indeterminate_segments)} segments...")
        
        # Créer un index des connexions
        connections = self._build_connection_index(indeterminate_segments)
        
        # Construire les chaînes
        chains = []
        used_segments = set()
        
        for segment in indeterminate_segments:
            if segment.way_id in used_segments:
                continue
            
            # Construire une chaîne à partir de ce segment
            chain, used_ids = self._build_chain_from_segment(segment, connections, used_segments)
            chains.append(chain)
            used_segments.update(used_ids)
        
        # Segments orphelins
        orphaned = [seg for seg in indeterminate_segments if seg.way_id not in used_segments]
        
        result = SimpleChainResult(chains=chains, orphaned_segments=orphaned)
        self._print_chain_statistics(result)
        return result
    
    def _build_connection_index(self, segments: List[MotorwayLink]) -> Dict[str, Dict[str, str]]:
        """
        Construit un index des connexions entre segments.
        
        Returns:
            Dict[way_id, Dict[connection_type, connected_way_id]]
        """
        print("   📋 Construction de l'index des connexions...")
        
        connections = {}
        
        for i, seg1 in enumerate(segments):
            connections[seg1.way_id] = {}
            
            for j, seg2 in enumerate(segments):
                if i == j:
                    continue
                
                # Test fin_seg1 → début_seg2
                if are_coordinates_equal(seg1.get_end_point(), seg2.get_start_point()):
                    connections[seg1.way_id][f"end_to_{seg2.way_id}_start"] = seg2.way_id
                
                # Test début_seg1 → fin_seg2
                if are_coordinates_equal(seg1.get_start_point(), seg2.get_end_point()):
                    connections[seg1.way_id][f"start_to_{seg2.way_id}_end"] = seg2.way_id
        
        total_connections = sum(len(conns) for conns in connections.values())
        print(f"   📊 {total_connections} connexions trouvées")
        
        return connections
    
    def _build_chain_from_segment(
        self, 
        start_segment: MotorwayLink, 
        connections: Dict[str, Dict[str, str]],
        used_segments: Set[str]
    ) -> Tuple[SimpleChain, Set[str]]:
        """
        Construit une chaîne à partir d'un segment de départ.
        
        Returns:
            Tuple[chaîne, segments_utilisés]
        """
        chain_segments = [start_segment]
        chain_used = {start_segment.way_id}
        
        # Étendre vers l'avant (fin du segment actuel)
        current_segment = start_segment
        while True:
            found_next = False
            segment_connections = connections.get(current_segment.way_id, {})
            
            for conn_key, next_way_id in segment_connections.items():
                if next_way_id in chain_used or next_way_id in used_segments:
                    continue
                
                # Vérifier si c'est une connexion "end_to_start"
                if conn_key.endswith("_start") and conn_key.startswith("end_to_"):
                    # Trouver le segment correspondant
                    next_segment = self._find_segment_by_way_id(next_way_id, chain_segments[0])
                    if next_segment:
                        chain_segments.append(next_segment)
                        chain_used.add(next_way_id)
                        current_segment = next_segment
                        found_next = True
                        break
            
            if not found_next:
                break
        
        # Étendre vers l'arrière (début du premier segment)
        current_segment = start_segment
        while True:
            found_prev = False
            
            # Chercher un segment dont la fin se connecte au début du segment actuel
            for way_id, segment_connections in connections.items():
                if way_id in chain_used or way_id in used_segments:
                    continue
                
                for conn_key, connected_way_id in segment_connections.items():
                    if connected_way_id == current_segment.way_id and conn_key.endswith("_start"):
                        # Trouver le segment correspondant
                        prev_segment = self._find_segment_by_way_id(way_id, chain_segments[0])
                        if prev_segment:
                            chain_segments.insert(0, prev_segment)
                            chain_used.add(way_id)
                            current_segment = prev_segment
                            found_prev = True
                            break
                
                if found_prev:
                    break
            
            if not found_prev:
                break
        
        chain = SimpleChain(
            chain_id=f"simple_chain_{start_segment.way_id}",
            segments=chain_segments
        )
        
        return chain, chain_used
    
    def _find_segment_by_way_id(self, way_id: str, reference_segment: MotorwayLink) -> Optional[MotorwayLink]:
        """Trouve un segment par son way_id (simulation - dans la vraie version, on aurait un index)."""
        # Cette fonction est un placeholder - en réalité, on devrait avoir un index
        # Pour le moment, on retourne None car on ne peut pas accéder à tous les segments
        return None
    
    def _print_chain_statistics(self, result: SimpleChainResult):
        """Affiche les statistiques de chaînage."""
        stats = result.get_stats()
        print(f"📊 Résultat du chaînage simple:")
        print(f"   • Chaînes créées: {stats['chains_count']}")
        print(f"   • Segments chaînés: {stats['total_chained_segments']}")
        print(f"   • Segments orphelins: {stats['orphaned_segments']}")
        print(f"   • Total segments: {stats['total_segments']}")
        
        if result.chains:
            chain_sizes = [chain.get_segment_count() for chain in result.chains]
            avg_size = sum(chain_sizes) / len(chain_sizes)
            print(f"   • Taille moyenne des chaînes: {avg_size:.1f} segments")
            print(f"   • Plus grande chaîne: {max(chain_sizes)} segments")
        
        print("✅ Construction simple des chaînes terminée!\n")
