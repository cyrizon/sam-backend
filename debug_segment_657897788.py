#!/usr/bin/env python3
"""
Debug Segment way/657897788
--------------------------

Recherche approfondie du segment way/657897788 dans toutes les données.
"""

import os
import sys

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cache.v2 import OSMDataManagerV2


def debug_segment():
    """Debug complet pour way/657897788."""
    print("🔍 Debug du segment way/657897788\n")
    
    target_segment = "way/657897788"
    
    # Initialiser le gestionnaire
    manager = OSMDataManagerV2(cache_dir="osm_cache_v2_test")
    project_root = os.path.dirname(__file__)
    data_sources = OSMDataManagerV2.get_default_data_sources(project_root)
    
    print("⏳ Chargement des données...")
    success = manager.initialize(data_sources)
    
    if not success:
        print("❌ Échec du chargement")
        return
    
    print("✅ Données chargées\n")
    
    # 1. Chercher dans les données parsées brutes
    print("🔍 1. Recherche dans les données parsées brutes:")
    
    # Entry links
    entry_links = manager._data.parsed_data.entry_links
    found_in_entries = [link for link in entry_links if link.way_id == target_segment]
    print(f"   • Entry links: {len(found_in_entries)} trouvé(s)")
    
    # Exit links  
    exit_links = manager._data.parsed_data.exit_links
    found_in_exits = [link for link in exit_links if link.way_id == target_segment]
    print(f"   • Exit links: {len(found_in_exits)} trouvé(s)")
    
    # Indeterminate links
    indeterminate_links = manager._data.parsed_data.indeterminate_links
    found_in_indeterminate = [link for link in indeterminate_links if link.way_id == target_segment]
    print(f"   • Indeterminate links: {len(found_in_indeterminate)} trouvé(s)")
    
    # 2. Afficher les détails du segment trouvé
    found_segment = None
    segment_type = None
    
    if found_in_entries:
        found_segment = found_in_entries[0]
        segment_type = "entry"
    elif found_in_exits:
        found_segment = found_in_exits[0]
        segment_type = "exit"
    elif found_in_indeterminate:
        found_segment = found_in_indeterminate[0]
        segment_type = "indeterminate"
    
    if found_segment:
        print(f"\n📍 2. Détails du segment trouvé (type: {segment_type}):")
        print(f"   • Way ID: {found_segment.way_id}")
        print(f"   • Type: {found_segment.link_type.value}")
        print(f"   • Destination: {found_segment.destination}")
        print(f"   • Points: {len(found_segment.coordinates)} coordonnées")
        print(f"   • Début: {found_segment.get_start_point()}")
        print(f"   • Fin: {found_segment.get_end_point()}")
    else:
        print(f"\n❌ Segment {target_segment} non trouvé dans les données parsées!")
        return
    
    # 3. Chercher dans les liens complets
    print(f"\n🔍 3. Recherche dans les liens complets:")
    all_complete_links = manager.get_all_complete_links()
    
    found_in_complete = []
    for complete_link in all_complete_links:
        segment_ids = [seg.way_id for seg in complete_link.segments]
        if target_segment in segment_ids:
            found_in_complete.append(complete_link)
    
    print(f"   • Trouvé dans {len(found_in_complete)} lien(s) complet(s)")
    
    # 4. Chercher dans les indéterminés non liés
    print(f"\n🔍 4. Recherche dans les indéterminés non liés:")
    unlinked = manager._data.linking_result.unlinked_indeterminate
    found_in_unlinked = [link for link in unlinked if link.way_id == target_segment]
    print(f"   • Trouvé dans {len(found_in_unlinked)} segment(s) non lié(s)")
    
    # 5. Si le segment était un entry/exit, voir pourquoi il n'a pas été lié
    if segment_type in ["entry", "exit"] and not found_in_complete:
        print(f"\n⚠️ 5. Analyse du problème de liaison:")
        print(f"   Le segment {target_segment} est un {segment_type} mais n'apparaît pas dans les liens complets!")
        
        # Chercher des segments indéterminés proches
        print(f"   Recherche de segments indéterminés à proximité (≤2m)...")
        nearby_segments = find_nearby_segments(found_segment, indeterminate_links, max_distance_m=2.0)
        print(f"   • Segments indéterminés à ≤2m: {len(nearby_segments)}")
        
        for i, (nearby_seg, distance) in enumerate(nearby_segments[:5]):  # Afficher les 5 premiers
            print(f"     {i+1}. {nearby_seg.way_id} - {distance:.1f}m")
    
    # 6. Rechercher les autres segments de la séquence attendue
    print(f"\n🔍 6. Recherche des autres segments de la séquence:")
    other_segments = ["way/126357480", "way/1298540619", "way/1298540620"]
    
    for other_seg in other_segments:
        found_in_data = find_segment_in_all_data(manager, other_seg)
        print(f"   • {other_seg}: {found_in_data}")


def find_segment_in_all_data(manager, segment_id):
    """Trouve un segment dans toutes les données."""
    # Parsed data
    entry_links = manager._data.parsed_data.entry_links
    exit_links = manager._data.parsed_data.exit_links
    indeterminate_links = manager._data.parsed_data.indeterminate_links
    
    if any(link.way_id == segment_id for link in entry_links):
        return "entry (parsé)"
    if any(link.way_id == segment_id for link in exit_links):
        return "exit (parsé)"
    if any(link.way_id == segment_id for link in indeterminate_links):
        return "indeterminate (parsé)"
    
    # Complete links
    all_complete_links = manager.get_all_complete_links()
    for complete_link in all_complete_links:
        segment_ids = [seg.way_id for seg in complete_link.segments]
        if segment_id in segment_ids:
            return f"dans lien complet {complete_link.link_id} ({complete_link.link_type.value})"
    
    # Unlinked
    unlinked = manager._data.linking_result.unlinked_indeterminate
    if any(link.way_id == segment_id for link in unlinked):
        return "indeterminate non lié"
    
    return "NON TROUVÉ"


def find_nearby_segments(target_segment, candidate_segments, max_distance_m=2.0):
    """Trouve les segments à proximité du segment cible."""
    from src.cache.utils.geographic_utils import calculate_distance
    
    nearby = []
    target_start = target_segment.get_start_point()
    target_end = target_segment.get_end_point()
    
    for candidate in candidate_segments:
        if candidate.way_id == target_segment.way_id:
            continue
        
        candidate_start = candidate.get_start_point()
        candidate_end = candidate.get_end_point()
        
        # Calculer toutes les distances possibles
        distances = [
            calculate_distance(target_start, candidate_start) * 1000,  # km -> m
            calculate_distance(target_start, candidate_end) * 1000,
            calculate_distance(target_end, candidate_start) * 1000,
            calculate_distance(target_end, candidate_end) * 1000
        ]
        
        min_distance = min(distances)
        if min_distance <= max_distance_m:
            nearby.append((candidate, min_distance))
    
    # Trier par distance
    nearby.sort(key=lambda x: x[1])
    return nearby


if __name__ == "__main__":
    debug_segment()
