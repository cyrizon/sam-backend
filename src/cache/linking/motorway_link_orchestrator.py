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
    
    def __init__(self, max_distance_m: float = 2.0, output_dir: str = None):
        """
        Initialise l'orchestrateur.
        
        Args:
            max_distance_m: Distance maximale pour lier deux segments (ignoré maintenant)
            output_dir: Répertoire de sortie pour les orphelins. Si None, utilise CACHE_DIR depuis l'environnement
        """
        # Utiliser la variable d'environnement si output_dir n'est pas fourni
        if output_dir is None:
            output_dir = os.getenv("CACHE_DIR", "./osm_cache_test")
            
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
        
        # Étape 2: Lier les entrées aux chaînes SEULEMENT
        print("🔗 Étape 2: Liaison des entrées aux chaînes")
        entry_links, used_chains_entry = self._link_entries_to_chains(
            entries, chain_result.chains
        )
        
        # Étape 3: Lier les sorties aux chaînes restantes
        print("🔗 Étape 3: Liaison des sorties aux chaînes restantes")
        exit_links, used_chains_exit = self._link_exits_to_chains(
            exits, chain_result.chains, used_chains_entry
        )
        
        # Étape 4: Créer des liens simples pour les segments non liés
        print("🔗 Étape 4: Création de liens simples pour les segments isolés")
        simple_links = self._create_simple_links(
            entries, exits, entry_links, exit_links
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
    
    def _link_entries_to_chains(
        self,
        entries: List[MotorwayLink],
        chains: List[CoordinateChain]
    ) -> Tuple[List[CompleteMotorwayLink], Set[str]]:
        """
        Lie les entrées aux chaînes SEULEMENT.
        Logique: entry_start -> chain_end (début de l'entrée = fin de la chaîne)
        
        Returns:
            Tuple[liens_créés, chaînes_utilisées]
        """
        entry_links = []
        used_chains = set()
        
        for entry in entries:
            # Chercher une chaîne qui finit où l'entrée commence
            linked_chain = self._find_chain_for_entry(entry, chains, used_chains)
            
            if linked_chain:
                # Créer le lien complet : [CHAÎNE] + [ENTRÉE]
                # Car on vient de la chaîne vers l'entrée
                segments = linked_chain.segments + [entry]
                
                complete_link = CompleteMotorwayLink(
                    link_id=f"entry_link_{entry.way_id}",
                    link_type=LinkType.ENTRY,
                    segments=segments,
                    destination=entry.destination
                )
                
                entry_links.append(complete_link)
                used_chains.add(linked_chain.chain_id)
        
        print(f"   • Liens d'entrée créés: {len(entry_links)}")
        return entry_links, used_chains

    def _link_exits_to_chains(
        self,
        exits: List[MotorwayLink],
        chains: List[CoordinateChain],
        used_chains: Set[str]
    ) -> Tuple[List[CompleteMotorwayLink], Set[str]]:
        """
        Lie les sorties aux chaînes restantes SEULEMENT.
        Logique: chain_start -> exit_end (début de la chaîne = fin de la sortie)
        
        Returns:
            Tuple[liens_créés, nouvelles_chaînes_utilisées]
        """
        exit_links = []
        newly_used_chains = set()
        
        # Chaînes disponibles (non utilisées par les entrées)
        available_chains = [c for c in chains if c.chain_id not in used_chains]
        
        for exit in exits:
            # Chercher une chaîne qui commence où la sortie finit
            linked_chain = self._find_chain_for_exit(exit, available_chains, newly_used_chains)
            
            if linked_chain:
                # Créer le lien complet : [SORTIE] + [CHAÎNE]
                # Car on va de la sortie vers la chaîne
                segments = [exit] + linked_chain.segments
                
                complete_link = CompleteMotorwayLink(
                    link_id=f"exit_link_{exit.way_id}",
                    link_type=LinkType.EXIT,
                    segments=segments,
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
        entry_links: List[CompleteMotorwayLink],
        exit_links: List[CompleteMotorwayLink]
    ) -> List[CompleteMotorwayLink]:
        """Crée des liens simples pour les segments isolés."""
        simple_links = []
        
        # Entrées utilisées dans les liens d'entrée (maintenant c'est le dernier segment)
        used_entries = {link.segments[-1].way_id for link in entry_links}
        
        # Sorties utilisées dans les liens de sortie (maintenant c'est le premier segment)
        used_exits_in_exit_links = {link.segments[0].way_id for link in exit_links}
        
        # Créer des liens simples pour les entrées non utilisées
        for entry in entries:
            if entry.way_id not in used_entries:
                simple_link = CompleteMotorwayLink(
                    link_id=f"entry_direct_{entry.way_id}",
                    link_type=LinkType.ENTRY,
                    segments=[entry],
                    destination=entry.destination
                )
                simple_links.append(simple_link)
        
        # Créer des liens simples pour les sorties non utilisées
        for exit in exits:
            if exit.way_id not in used_exits_in_exit_links:
                simple_link = CompleteMotorwayLink(
                    link_id=f"exit_direct_{exit.way_id}",
                    link_type=LinkType.EXIT,
                    segments=[exit],
                    destination=exit.destination
                )
                simple_links.append(simple_link)
        
        print(f"   • Liens simples créés: {len(simple_links)}")
        return simple_links
    
    def _find_chain_for_entry(
        self,
        entry: MotorwayLink,
        chains: List[CoordinateChain],
        used_chains: Set[str]
    ) -> Optional[CoordinateChain]:
        """
        Trouve une chaîne pour une entrée.
        Logique: entry_start -> chain_end (début de l'entrée = fin de la chaîne)
        """
        for chain in chains:
            if chain.chain_id in used_chains:
                continue
            
            # Test connexion : début de l'entrée = fin de la chaîne
            if are_coordinates_equal(entry.get_start_point(), chain.get_end_point()):
                return chain
        
        return None
    
    def _find_chain_for_exit(
        self,
        exit: MotorwayLink,
        chains: List[CoordinateChain],
        used_chains: Set[str]
    ) -> Optional[CoordinateChain]:
        """
        Trouve une chaîne pour une sortie.
        Logique: chain_start -> exit_end (début de la chaîne = fin de la sortie)
        """
        for chain in chains:
            if chain.chain_id in used_chains:
                continue
            
            # Test connexion : début de la chaîne = fin de la sortie
            if are_coordinates_equal(chain.get_start_point(), exit.get_end_point()):
                return chain
        
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
