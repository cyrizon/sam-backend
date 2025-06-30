"""
Coordinate-Based Chain Builder
-----------------------------

Constructeur de chaînes basé uniquement sur la correspondance exacte des coordonnées.
"""

from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

from ..models.motorway_link import MotorwayLink
from ..models.link_types import LinkType
from .coordinate_matcher import are_coordinates_equal


@dataclass
class CoordinateChain:
    """Chaîne de segments connectés par coordonnées."""
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
class CoordinateChainResult:
    """Résultat de la construction des chaînes."""
    chains: List[CoordinateChain]
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


class CoordinateChainBuilder:
    """Constructeur de chaînes basé sur les coordonnées."""
    
    def __init__(self):
        """Initialise le constructeur."""
        pass
    
    def build_chains(self, indeterminate_segments: List[MotorwayLink]) -> CoordinateChainResult:
        """
        Construit des chaînes à partir des segments indéterminés.
        
        Args:
            indeterminate_segments: Segments indéterminés à chaîner
            
        Returns:
            CoordinateChainResult: Résultat du chaînage
        """
        print(f"🔗 Construction des chaînes par coordonnées ({len(indeterminate_segments)} segments)...")
        
        # Créer des index par coordonnées
        start_points = self._create_coordinate_index(indeterminate_segments, 'start')
        end_points = self._create_coordinate_index(indeterminate_segments, 'end')
        
        # Construire les chaînes
        chains = []
        used_segments = set()
        
        for segment in indeterminate_segments:
            if segment.way_id in used_segments:
                continue
            
            # Construire une chaîne à partir de ce segment
            chain_segments = self._build_chain_from_segment_v2(
                segment, start_points, end_points, used_segments
            )
            
            if chain_segments:
                chain = CoordinateChain(
                    chain_id=f"coord_chain_{len(chains) + 1}",
                    segments=chain_segments
                )
                chains.append(chain)
                used_segments.update(seg.way_id for seg in chain_segments)
        
        # Segments orphelins
        orphaned = [seg for seg in indeterminate_segments if seg.way_id not in used_segments]
        
        result = CoordinateChainResult(chains=chains, orphaned_segments=orphaned)
        self._print_chain_statistics(result)
        return result
    
    def _create_coordinate_index(
        self, 
        segments: List[MotorwayLink], 
        point_type: str
    ) -> Dict[str, List[MotorwayLink]]:
        """
        Crée un index des segments par coordonnées.
        
        Args:
            segments: Liste des segments
            point_type: 'start' ou 'end'
            
        Returns:
            Dict[coord_key, List[segments]]
        """
        index = defaultdict(list)
        
        for segment in segments:
            if point_type == 'start':
                point = segment.get_start_point()
            else:
                point = segment.get_end_point()
            
            # Créer une clé basée sur les coordonnées (arrondie à 7 décimales)
            coord_key = f"{point[0]:.7f},{point[1]:.7f}"
            index[coord_key].append(segment)
        
        return dict(index)
    
    def _build_chain_from_segment_v2(
        self,
        start_segment: MotorwayLink,
        start_points: Dict[str, List[MotorwayLink]],
        end_points: Dict[str, List[MotorwayLink]],
        used_segments: Set[str]
    ) -> List[MotorwayLink]:
        """
        Construit une chaîne à partir d'un segment de départ.
        
        Returns:
            List[MotorwayLink]: Segments de la chaîne
        """
        if start_segment.way_id in used_segments:
            return []
        
        chain = [start_segment]
        
        # Étendre vers l'avant (fin → début)
        current_segment = start_segment
        while True:
            end_point = current_segment.get_end_point()
            coord_key = f"{end_point[0]:.7f},{end_point[1]:.7f}"
            
            # Chercher des segments qui commencent à cette coordonnée
            next_candidates = start_points.get(coord_key, [])
            
            found_next = False
            for candidate in next_candidates:
                if candidate.way_id != current_segment.way_id and candidate.way_id not in used_segments:
                    # Vérifier que ce segment n'est pas déjà dans la chaîne
                    if candidate not in chain:
                        chain.append(candidate)
                        current_segment = candidate
                        found_next = True
                        break
            
            if not found_next:
                break
        
        # Étendre vers l'arrière (début ← fin)
        current_segment = start_segment
        while True:
            start_point = current_segment.get_start_point()
            coord_key = f"{start_point[0]:.7f},{start_point[1]:.7f}"
            
            # Chercher des segments qui finissent à cette coordonnée
            prev_candidates = end_points.get(coord_key, [])
            
            found_prev = False
            for candidate in prev_candidates:
                if candidate.way_id != current_segment.way_id and candidate.way_id not in used_segments:
                    # Vérifier que ce segment n'est pas déjà dans la chaîne
                    if candidate not in chain:
                        chain.insert(0, candidate)
                        current_segment = candidate
                        found_prev = True
                        break
            
            if not found_prev:
                break
        
        return chain
    
    def _print_chain_statistics(self, result: CoordinateChainResult):
        """Affiche les statistiques de chaînage."""
        stats = result.get_stats()
        print(f"📊 Résultat du chaînage par coordonnées:")
        print(f"   • Chaînes créées: {stats['chains_count']}")
        print(f"   • Segments chaînés: {stats['total_chained_segments']}")
        print(f"   • Segments orphelins: {stats['orphaned_segments']}")
        print(f"   • Total segments: {stats['total_segments']}")
        
        if result.chains:
            chain_sizes = [chain.get_segment_count() for chain in result.chains]
            avg_size = sum(chain_sizes) / len(chain_sizes)
            print(f"   • Taille moyenne des chaînes: {avg_size:.1f} segments")
            print(f"   • Plus grande chaîne: {max(chain_sizes)} segments")
            
            # Afficher quelques exemples de chaînes
            print(f"   • Exemples de chaînes:")
            for i, chain in enumerate(result.chains[:3]):
                way_ids = [seg.way_id for seg in chain.segments]
                print(f"     Chaîne {i+1}: {' → '.join(way_ids[:5])}{'...' if len(way_ids) > 5 else ''}")
        
        print("✅ Construction des chaînes par coordonnées terminée!\n")
