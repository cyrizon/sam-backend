#!/usr/bin/env python3
"""
Verification Script - Link Sequence
----------------------------------

Vérifie si la séquence spécifique 657897788,126357480,1298540619,1298540620
a été correctement reconstruite dans les liens complets.
"""

import os
import sys

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cache.v2 import OSMDataManagerV2


def find_link_sequence():
    """Recherche la séquence spécifique dans les liens complets."""
    print("🔍 Recherche de la séquence: 657897788,126357480,1298540619,1298540620\n")
    
    # Séquence recherchée
    target_sequence = ["way/657897788", "way/126357480", "way/1298540619", "way/1298540620"]
    print(f"🎯 Séquence cible: {' → '.join(target_sequence)}\n")
    
    # Initialiser le gestionnaire
    manager = OSMDataManagerV2()
    project_root = os.path.dirname(__file__)
    data_sources = OSMDataManagerV2.get_default_data_sources(project_root)
    
    print("⏳ Initialisation du gestionnaire...")
    success = manager.initialize(data_sources)
    
    if not success:
        print("❌ Échec de l'initialisation")
        return
    
    print("✅ Gestionnaire initialisé\n")
    
    # Rechercher dans tous les liens complets
    all_complete_links = manager.get_all_complete_links()
    print(f"🔍 Recherche dans {len(all_complete_links)} liens complets...\n")
    
    found_sequences = []
    
    for complete_link in all_complete_links:
        # Obtenir les way_ids de tous les segments de ce lien
        segment_ids = [segment.way_id for segment in complete_link.segments]
        
        # Vérifier si la séquence cible est contenue dans ce lien
        if contains_sequence(segment_ids, target_sequence):
            found_sequences.append((complete_link, segment_ids))
            
        # Vérifier aussi des sous-séquences partielles
        for i in range(len(target_sequence)):
            for j in range(i + 2, len(target_sequence) + 1):
                partial_sequence = target_sequence[i:j]
                if len(partial_sequence) >= 2 and contains_sequence(segment_ids, partial_sequence):
                    # Éviter les doublons
                    if not any(partial_sequence == target_sequence for _, _ in found_sequences):
                        print(f"🔍 Séquence partielle trouvée: {' → '.join(partial_sequence)}")
                        print(f"   Dans le lien: {complete_link.link_id} ({complete_link.link_type.value})")
                        print(f"   Segments complets: {' → '.join(segment_ids[:10])}{'...' if len(segment_ids) > 10 else ''}")
                        print(f"   Total segments: {len(segment_ids)}")
                        if complete_link.has_toll():
                            print(f"   Péage associé: {complete_link.associated_toll.display_name}")
                        print()
    
    # Afficher les résultats
    if found_sequences:
        print(f"🎉 Séquence complète trouvée dans {len(found_sequences)} lien(s)!")
        
        for complete_link, segment_ids in found_sequences:
            print(f"\n✅ Lien trouvé: {complete_link.link_id}")
            print(f"   Type: {complete_link.link_type.value}")
            print(f"   Nombre de segments: {len(segment_ids)}")
            print(f"   Séquence complète: {' → '.join(segment_ids)}")
            
            if complete_link.has_toll():
                print(f"   Péage associé: {complete_link.associated_toll.display_name}")
                print(f"   Distance péage: {complete_link.toll_distance_meters:.1f}m")
            
            if complete_link.destination:
                print(f"   Destination: {complete_link.destination}")
            
            print(f"   Coordonnées début: {complete_link.get_start_point()}")
            print(f"   Coordonnées fin: {complete_link.get_end_point()}")
            
            # Vérifier la position de la séquence cible
            start_idx = find_sequence_start(segment_ids, target_sequence)
            if start_idx >= 0:
                print(f"   Position de la séquence: segments {start_idx} à {start_idx + len(target_sequence) - 1}")
    else:
        print("❌ Séquence complète non trouvée")
        
        # Rechercher des segments individuels
        print("\n🔍 Recherche des segments individuels...")
        search_individual_segments(manager, target_sequence)


def contains_sequence(haystack, needle):
    """Vérifie si needle est une sous-séquence de haystack."""
    if len(needle) > len(haystack):
        return False
    
    for i in range(len(haystack) - len(needle) + 1):
        if haystack[i:i + len(needle)] == needle:
            return True
    return False


def find_sequence_start(haystack, needle):
    """Trouve l'index de début de needle dans haystack."""
    for i in range(len(haystack) - len(needle) + 1):
        if haystack[i:i + len(needle)] == needle:
            return i
    return -1


def search_individual_segments(manager, target_sequence):
    """Recherche des segments individuels dans tous les liens."""
    all_complete_links = manager.get_all_complete_links()
    
    for target_id in target_sequence:
        print(f"\n🔍 Recherche du segment: {target_id}")
        found_in_links = []
        
        for complete_link in all_complete_links:
            segment_ids = [segment.way_id for segment in complete_link.segments]
            if target_id in segment_ids:
                position = segment_ids.index(target_id)
                found_in_links.append((complete_link, position))
        
        if found_in_links:
            print(f"   ✅ Trouvé dans {len(found_in_links)} lien(s):")
            for complete_link, position in found_in_links:
                print(f"      • {complete_link.link_id} ({complete_link.link_type.value}) - position {position}")
        else:
            print(f"   ❌ Non trouvé dans les liens complets")


if __name__ == "__main__":
    find_link_sequence()
