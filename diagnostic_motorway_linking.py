"""
Diagnostic du système de liaison
--------------------------------

Analyse les données OSM pour diagnostiquer les problèmes de liaison.
"""

import os
import sys
import json

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cache.v2.parsers.motorway_segments_parser import MotorwaySegmentsParser
from src.cache.v2.models.link_types import LinkType
from src.cache.v2.linking.coordinate_matcher import SegmentConnectionAnalyzer


def analyze_segment_data():
    """Analyse les données des segments pour diagnostiquer les problèmes."""
    print("🔍 Analyse des données de segments motorway")
    print("=" * 50)
    
    # Chemins des fichiers
    data_dir = "data"
    osm_dir = os.path.join(data_dir, "osm")
    
    entries_path = os.path.join(osm_dir, "motorway_entries.geojson")
    exits_path = os.path.join(osm_dir, "motorway_exits.geojson")
    indeterminates_path = os.path.join(osm_dir, "motorway_indeterminate.geojson")
    
    parser = MotorwaySegmentsParser()
    
    # Charger les segments
    print("📥 Chargement des segments...")
    entries = parser.parse_segments(entries_path, LinkType.ENTRY)
    exits = parser.parse_segments(exits_path, LinkType.EXIT)
    indeterminates = parser.parse_segments(indeterminates_path, LinkType.INDETERMINATE)
    
    print(f"   Entrées: {len(entries)}")
    print(f"   Sorties: {len(exits)}")
    print(f"   Indéterminés: {len(indeterminates)}")
    
    # Analyser les coordonnées
    print("\n🎯 Analyse des coordonnées...")
    analyze_coordinates_distribution(entries, exits, indeterminates)
    
    # Tester les connexions
    print("\n🔗 Test des connexions possibles...")
    test_potential_connections(entries[:10], exits[:10], indeterminates[:100])
    
    # Analyser les segments indéterminés spécifiquement
    print("\n🔀 Analyse des segments indéterminés...")
    analyze_indeterminate_segments(indeterminates[:50])


def analyze_coordinates_distribution(entries, exits, indeterminates):
    """Analyse la distribution des coordonnées."""
    def get_coord_stats(segments, name):
        if not segments:
            return
        
        lons = []
        lats = []
        for seg in segments:
            if seg.coordinates:
                for coord in seg.coordinates:
                    if len(coord) >= 2:
                        lons.append(coord[0])
                        lats.append(coord[1])
        
        if lons and lats:
            print(f"   {name}:")
            print(f"     Longitude: {min(lons):.4f} à {max(lons):.4f}")
            print(f"     Latitude: {min(lats):.4f} à {max(lats):.4f}")
            print(f"     Points: {len(lons)}")
    
    get_coord_stats(entries, "Entrées")
    get_coord_stats(exits, "Sorties")
    get_coord_stats(indeterminates, "Indéterminés")


def test_potential_connections(entries, exits, indeterminates):
    """Test les connexions potentielles entre segments."""
    analyzer = SegmentConnectionAnalyzer(max_distance_m=2.0)
    
    connections_found = 0
    total_tests = 0
    
    # Test entrées -> indéterminés
    print("   🔍 Test entrées -> indéterminés...")
    for entry in entries:
        for indet in indeterminates:
            total_tests += 1
            can_connect, connection_type, reason = analyzer.find_connection_type(
                entry.get_start_point(), entry.get_end_point(),
                indet.get_start_point(), indet.get_end_point()
            )
            if can_connect:
                connections_found += 1
                print(f"      ✅ Connexion trouvée: {entry.way_id} -> {indet.way_id} ({connection_type})")
                if connections_found >= 3:  # Limiter l'affichage
                    break
        if connections_found >= 3:
            break
    
    # Test indéterminés -> sorties
    print("   🔍 Test indéterminés -> sorties...")
    for indet in indeterminates:
        for exit in exits:
            total_tests += 1
            can_connect, connection_type, reason = analyzer.find_connection_type(
                indet.get_start_point(), indet.get_end_point(),
                exit.get_start_point(), exit.get_end_point()
            )
            if can_connect:
                connections_found += 1
                print(f"      ✅ Connexion trouvée: {indet.way_id} -> {exit.way_id} ({connection_type})")
                if connections_found >= 6:  # Limiter l'affichage
                    break
        if connections_found >= 6:
            break
    
    # Test indéterminés entre eux
    print("   🔍 Test indéterminés entre eux...")
    for i, indet1 in enumerate(indeterminates):
        for indet2 in indeterminates[i+1:]:
            total_tests += 1
            can_connect, connection_type, reason = analyzer.find_connection_type(
                indet1.get_start_point(), indet1.get_end_point(),
                indet2.get_start_point(), indet2.get_end_point()
            )
            if can_connect:
                connections_found += 1
                print(f"      ✅ Connexion trouvée: {indet1.way_id} -> {indet2.way_id} ({connection_type})")
                if connections_found >= 10:  # Limiter l'affichage
                    break
        if connections_found >= 10:
            break
    
    print(f"   📊 Résumé: {connections_found} connexions sur {total_tests} tests")


def analyze_indeterminate_segments(indeterminates):
    """Analyse spécifique des segments indéterminés."""
    if not indeterminates:
        return
    
    print(f"   Analysant {len(indeterminates)} segments indéterminés...")
    
    # Analyser les propriétés
    properties_analysis = {}
    way_ids = set()
    coordinate_counts = []
    
    for seg in indeterminates:
        way_ids.add(seg.way_id)
        coordinate_counts.append(len(seg.coordinates) if seg.coordinates else 0)
        
        # Analyser les propriétés
        for key, value in seg.properties.items():
            if key not in properties_analysis:
                properties_analysis[key] = set()
            properties_analysis[key].add(str(value)[:50])  # Limiter la longueur
    
    print(f"   Way IDs uniques: {len(way_ids)}")
    print(f"   Coordonnées par segment: {min(coordinate_counts)} à {max(coordinate_counts)}")
    print(f"   Moyenne coordonnées: {sum(coordinate_counts)/len(coordinate_counts):.1f}")
    
    # Afficher les propriétés les plus communes
    print("   Propriétés communes:")
    for key, values in properties_analysis.items():
        if len(values) <= 10:  # Afficher seulement les propriétés avec peu de valeurs
            print(f"     {key}: {list(values)[:5]}")
    
    # Analyser quelques segments en détail
    print("\n   📋 Détails de quelques segments:")
    for i, seg in enumerate(indeterminates[:3]):
        print(f"     Segment {i+1}:")
        print(f"       Way ID: {seg.way_id}")
        print(f"       Coordonnées: {len(seg.coordinates)} points")
        if seg.coordinates:
            print(f"       Début: {seg.get_start_point()}")
            print(f"       Fin: {seg.get_end_point()}")
        print(f"       Propriétés: {list(seg.properties.keys())[:5]}")


def check_orphaned_segments():
    """Vérifie les segments orphelins générés."""
    orphaned_file = os.path.join("osm_cache_v2_test", "orphaned_segments.json")
    
    if os.path.exists(orphaned_file):
        print(f"\n🗂️  Analyse des segments orphelins...")
        
        with open(orphaned_file, 'r', encoding='utf-8') as f:
            orphaned_data = json.load(f)
        
        unused_chains = orphaned_data.get('unused_chains', [])
        orphaned_individual = orphaned_data.get('orphaned_individual_segments', [])
        
        print(f"   Chaînes non utilisées: {len(unused_chains)}")
        print(f"   Segments individuels orphelins: {len(orphaned_individual)}")
        
        # Analyser les chaînes non utilisées
        if unused_chains:
            for i, chain in enumerate(unused_chains[:3]):
                print(f"   Chaîne {i+1}:")
                print(f"     ID: {chain['chain_id']}")
                print(f"     Segments: {chain['segment_count']}")
                if chain['segments']:
                    first_seg = chain['segments'][0]
                    print(f"     Premier segment: {first_seg.get('way_id', 'N/A')}")
        
        # Analyser les segments individuels
        if orphaned_individual:
            print(f"   Exemples de segments orphelins:")
            for i, seg in enumerate(orphaned_individual[:3]):
                print(f"     Segment {i+1}: {seg.get('way_id', 'N/A')}")


if __name__ == "__main__":
    analyze_segment_data()
    check_orphaned_segments()
