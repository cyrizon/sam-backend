"""
Motorway Link Orchestrator
--------------------------

Orchestrates the complete motorway link building process:
1. Chains indeterminate segments
2. Links entries to chains
3. Links chains to exits
4. Outputs orphaned segments to JSON
"""

import json
import os
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import asdict

from ..models.motorway_link import MotorwayLink
from ..models.complete_motorway_link import CompleteMotorwayLink
from ..models.link_types import LinkType
from .coordinate_matcher import SegmentConnectionAnalyzer, are_coordinates_equal
from .coordinate_chain_builder import CoordinateChainBuilder, CoordinateChain


class MotorwayLinkOrchestrator:
    """Orchestrateur principal pour la construction des liens complets."""
    
    def __init__(self, max_distance_m: float = 2.0, output_dir: str = "osm_cache_v2_test"):
        """
        Initialise l'orchestrateur.
        
        Args:
            max_distance_m: Distance maximale pour lier deux segments (ignoré maintenant)
            output_dir: Répertoire de sortie pour les orphelins
        """
        self.analyzer = SegmentConnectionAnalyzer(max_distance_m)
        self.chain_builder = CoordinateChainBuilder()
        self.output_dir = output_dir
        self.max_distance_m = max_distance_m
    
    def build_complete_links(
        self,
        entries: List[MotorwayLink],
        exits: List[MotorwayLink],
        indeterminates: List[MotorwayLink]
    ) -> Tuple[List[CompleteMotorwayLink], Dict[str, any]]:
        """
        Construit les liens complets à partir des segments d'entrée, sortie et indéterminés.
        
        Args:
            entries: Segments d'entrée
            exits: Segments de sortie
            indeterminates: Segments indéterminés
            
        Returns:
            Tuple[liens_complets, statistiques]
        """
        print("🏗️  Début de la construction des liens complets...")
        print(f"   • Entrées: {len(entries)}")
        print(f"   • Sorties: {len(exits)}")
        print(f"   • Indéterminés: {len(indeterminates)}")
        
        # Étape 1: Chaîner les segments indéterminés
        print("\n🔗 Étape 1: Construction des chaînes de segments indéterminés")
        chain_result = self.chain_builder.build_chains(indeterminates)
        
        # Étape 2: Lier les entrées aux chaînes et aux sorties
        print("🔗 Étape 2: Liaison des entrées aux chaînes et sorties")
        entry_links, used_chains_entry, used_exits_entry = self._link_entries_to_destinations(
            entries, chain_result.chains, exits
        )
        
        # Étape 3: Lier les sorties aux chaînes restantes
        print("🔗 Étape 3: Liaison des sorties aux chaînes restantes")
        exit_links, used_chains_exit = self._link_exits_to_chains(
            exits, chain_result.chains, used_exits_entry, used_chains_entry
        )
        
        # Étape 4: Créer des liens simples pour les segments non liés
        print("🔗 Étape 4: Création de liens simples pour les segments isolés")
        simple_links = self._create_simple_links(
            entries, exits, used_exits_entry, entry_links, exit_links
        )
        
        # Collecter tous les liens complets
        all_complete_links = entry_links + exit_links + simple_links
        
        # Étape 5: Gérer les orphelins
        print("🗂️  Étape 5: Gestion des segments orphelins")
        used_chains_all = used_chains_entry | used_chains_exit
        orphaned_data = self._handle_orphaned_segments(
            chain_result, used_chains_all
        )
        
        # Statistiques finales
        stats = self._generate_final_statistics(
            entries, exits, indeterminates, all_complete_links, orphaned_data
        )
        
        self._print_final_summary(stats)
        
        return all_complete_links, stats
    
    def _link_entries_to_destinations(
        self,
        entries: List[MotorwayLink],
        chains: List[CoordinateChain],
        exits: List[MotorwayLink]
    ) -> Tuple[List[CompleteMotorwayLink], Set[str], Set[str]]:
        """
        Lie les entrées aux chaînes ou directement aux sorties.
        
        Returns:
            Tuple[liens_créés, chaînes_utilisées, sorties_utilisées]
        """
        entry_links = []
        used_chains = set()
        used_exits = set()
        
        for entry in entries:
            # Chercher une liaison avec une chaîne
            linked_chain = self._find_linkable_chain(entry, chains, used_chains)
            
            if linked_chain:
                # Chercher une sortie connectée à cette chaîne
                connected_exit = self._find_exit_connected_to_chain(
                    linked_chain, exits, used_exits
                )
                
                segments = [entry] + linked_chain.segments
                if connected_exit:
                    segments.append(connected_exit)
                    used_exits.add(connected_exit.way_id)
                
                complete_link = CompleteMotorwayLink(
                    link_id=f"entry_link_{entry.way_id}",
                    link_type=LinkType.ENTRY,
                    segments=segments,
                    destination=entry.destination
                )
                
                entry_links.append(complete_link)
                used_chains.add(linked_chain.chain_id)
                
            else:
                # Chercher une liaison directe avec une sortie
                connected_exit = self._find_directly_connected_exit(
                    entry, exits, used_exits
                )
                
                if connected_exit:
                    complete_link = CompleteMotorwayLink(
                        link_id=f"entry_direct_{entry.way_id}",
                        link_type=LinkType.ENTRY,
                        segments=[entry, connected_exit],
                        destination=entry.destination
                    )
                    
                    entry_links.append(complete_link)
                    used_exits.add(connected_exit.way_id)
        
        print(f"   • Liens d'entrée créés: {len(entry_links)}")
        return entry_links, used_chains, used_exits
    
    def _link_exits_to_chains(
        self,
        exits: List[MotorwayLink],
        chains: List[CoordinateChain],
        used_exits: Set[str],
        used_chains: Set[str]
    ) -> Tuple[List[CompleteMotorwayLink], Set[str]]:
        """
        Lie les sorties restantes aux chaînes restantes.
        
        Returns:
            Tuple[liens_créés, nouvelles_chaînes_utilisées]
        """
        exit_links = []
        newly_used_chains = set()
        
        available_exits = [e for e in exits if e.way_id not in used_exits]
        available_chains = [c for c in chains if c.chain_id not in used_chains]
        
        for exit in available_exits:
            linked_chain = self._find_linkable_chain(exit, available_chains, newly_used_chains)
            
            if linked_chain:
                complete_link = CompleteMotorwayLink(
                    link_id=f"exit_link_{exit.way_id}",
                    link_type=LinkType.EXIT,
                    segments=linked_chain.segments + [exit],
                    destination=exit.destination
                )
                
                exit_links.append(complete_link)
                newly_used_chains.add(linked_chain.chain_id)
        
        print(f"   • Liens de sortie créés: {len(exit_links)}")
        return exit_links, newly_used_chains
    
    def _create_simple_links(
        self,
        entries: List[MotorwayLink],
        exits: List[MotorwayLink],
        used_exits: Set[str],
        entry_links: List[CompleteMotorwayLink],
        exit_links: List[CompleteMotorwayLink]
    ) -> List[CompleteMotorwayLink]:
        """Crée des liens simples pour les segments isolés."""
        simple_links = []
        
        # Entrées utilisées dans les liens d'entrée
        used_entries = {link.segments[0].way_id for link in entry_links}
        
        # Sorties utilisées dans les liens de sortie
        used_exits_in_exit_links = {link.segments[-1].way_id for link in exit_links}
        all_used_exits = used_exits | used_exits_in_exit_links
        
        # Créer des liens simples pour les entrées non utilisées
        for entry in entries:
            if entry.way_id not in used_entries:
                simple_link = CompleteMotorwayLink(
                    link_id=f"simple_entry_{entry.way_id}",
                    link_type=LinkType.ENTRY,
                    segments=[entry],
                    destination=entry.destination
                )
                simple_links.append(simple_link)
        
        # Créer des liens simples pour les sorties non utilisées
        for exit in exits:
            if exit.way_id not in all_used_exits:
                simple_link = CompleteMotorwayLink(
                    link_id=f"simple_exit_{exit.way_id}",
                    link_type=LinkType.EXIT,
                    segments=[exit],
                    destination=exit.destination
                )
                simple_links.append(simple_link)
        
        print(f"   • Liens simples créés: {len(simple_links)}")
        return simple_links
    
    def _find_linkable_chain(
        self,
        segment: MotorwayLink,
        chains: List[CoordinateChain],
        used_chains: Set[str]
    ) -> Optional[CoordinateChain]:
        """Trouve une chaîne qui peut être liée au segment."""
        for chain in chains:
            if chain.chain_id in used_chains:
                continue
            
            # Test connexion avec le début de la chaîne (segment_end -> chain_start)
            if are_coordinates_equal(segment.get_end_point(), chain.get_start_point()):
                return chain
            
            # Test connexion avec la fin de la chaîne (segment_end -> chain_end - chaîne inversée)
            if are_coordinates_equal(segment.get_end_point(), chain.get_end_point()):
                return chain
        
        return None
    
    def _find_exit_connected_to_chain(
        self,
        chain: CoordinateChain,
        exits: List[MotorwayLink],
        used_exits: Set[str]
    ) -> Optional[MotorwayLink]:
        """Trouve une sortie connectée à la chaîne."""
        for exit in exits:
            if exit.way_id in used_exits:
                continue
            
            # Test connexion chain_end -> exit_start
            if are_coordinates_equal(chain.get_end_point(), exit.get_start_point()):
                return exit
        
        return None
    
    def _find_directly_connected_exit(
        self,
        entry: MotorwayLink,
        exits: List[MotorwayLink],
        used_exits: Set[str]
    ) -> Optional[MotorwayLink]:
        """Trouve une sortie directement connectée à l'entrée."""
        for exit in exits:
            if exit.way_id in used_exits:
                continue
            
            # Test connexion entry_end -> exit_start
            if are_coordinates_equal(entry.get_end_point(), exit.get_start_point()):
                return exit
        
        return None
    
    def _handle_orphaned_segments(
        self,
        chain_result,
        used_chains: Set[str]
    ) -> Dict[str, any]:
        """Gère les segments orphelins et les sauvegarde en JSON."""
        unused_chains = [
            chain for chain in chain_result.chains
            if chain.chain_id not in used_chains
        ]
        
        orphaned_data = {
            "unused_chains": [],
            "orphaned_individual_segments": []
        }
        
        # Chaînes non utilisées
        for chain in unused_chains:
            chain_data = {
                "chain_id": chain.chain_id,
                "segment_count": chain.get_segment_count(),
                "segments": [
                    {
                        "way_id": seg.way_id,
                        "coordinates": seg.coordinates,
                        "properties": seg.properties
                    }
                    for seg in chain.segments
                ]
            }
            orphaned_data["unused_chains"].append(chain_data)
        
        # Segments individuels orphelins
        for segment in chain_result.orphaned_segments:
            segment_data = {
                "way_id": segment.way_id,
                "coordinates": segment.coordinates,
                "properties": segment.properties
            }
            orphaned_data["orphaned_individual_segments"].append(segment_data)
        
        # Sauvegarder en JSON
        self._save_orphaned_segments(orphaned_data)
        
        return orphaned_data
    
    def _save_orphaned_segments(self, orphaned_data: Dict[str, any]):
        """Sauvegarde les segments orphelins en JSON."""
        output_file = os.path.join(self.output_dir, "orphaned_segments.json")
        
        # Créer le répertoire si nécessaire
        os.makedirs(self.output_dir, exist_ok=True)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(orphaned_data, f, indent=2, ensure_ascii=False)
            
            print(f"   • Segments orphelins sauvegardés: {output_file}")
        except Exception as e:
            print(f"   ⚠️  Erreur lors de la sauvegarde des orphelins: {e}")
    
    def _generate_final_statistics(
        self,
        entries: List[MotorwayLink],
        exits: List[MotorwayLink],
        indeterminates: List[MotorwayLink],
        complete_links: List[CompleteMotorwayLink],
        orphaned_data: Dict[str, any]
    ) -> Dict[str, any]:
        """Génère les statistiques finales."""
        return {
            "input_segments": {
                "entries": len(entries),
                "exits": len(exits),
                "indeterminates": len(indeterminates),
                "total": len(entries) + len(exits) + len(indeterminates)
            },
            "output_links": {
                "complete_links": len(complete_links),
                "entry_links": len([l for l in complete_links if l.link_type == LinkType.ENTRY]),
                "exit_links": len([l for l in complete_links if l.link_type == LinkType.EXIT])
            },
            "orphaned": {
                "unused_chains": len(orphaned_data["unused_chains"]),
                "orphaned_segments": len(orphaned_data["orphaned_individual_segments"])
            },
            "linking_efficiency": {
                "segments_in_complete_links": sum(len(link.segments) for link in complete_links),
                "usage_percentage": round(
                    (sum(len(link.segments) for link in complete_links) / 
                     (len(entries) + len(exits) + len(indeterminates))) * 100, 2
                )
            }
        }
    
    def _print_final_summary(self, stats: Dict[str, any]):
        """Affiche le résumé final."""
        print(f"\n📊 RÉSUMÉ FINAL DE LA CONSTRUCTION DES LIENS")
        print(f"═══════════════════════════════════════════")
        print(f"📥 Segments d'entrée:")
        print(f"   • Entrées: {stats['input_segments']['entries']}")
        print(f"   • Sorties: {stats['input_segments']['exits']}")
        print(f"   • Indéterminés: {stats['input_segments']['indeterminates']}")
        print(f"   • Total: {stats['input_segments']['total']}")
        
        print(f"\n📤 Liens complets créés:")
        print(f"   • Liens d'entrée: {stats['output_links']['entry_links']}")
        print(f"   • Liens de sortie: {stats['output_links']['exit_links']}")
        print(f"   • Total: {stats['output_links']['complete_links']}")
        
        print(f"\n🗂️  Segments orphelins:")
        print(f"   • Chaînes non utilisées: {stats['orphaned']['unused_chains']}")
        print(f"   • Segments individuels: {stats['orphaned']['orphaned_segments']}")
        
        print(f"\n⚡ Efficacité de liaison:")
        print(f"   • Segments utilisés: {stats['linking_efficiency']['segments_in_complete_links']}")
        print(f"   • Pourcentage d'utilisation: {stats['linking_efficiency']['usage_percentage']}%")
        
        print(f"\n✅ Construction des liens complets terminée!\n")
