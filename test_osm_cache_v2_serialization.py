#!/usr/bin/env python3
"""
Test OSM Cache V2 avec Sérialisation
------------------------------------

Test du système complet avec cache sérialisé.
"""

import os
import sys
import time

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cache.v2 import OSMDataManagerV2


def test_with_serialization():
    """Test complet avec sérialisation."""
    print("🧪 Test OSM Cache V2 avec Sérialisation\n")
    
    # 1. Initialiser le gestionnaire avec cache
    manager = OSMDataManagerV2(cache_dir="osm_cache_v2_test")
    
    # 2. Sources de données
    project_root = os.path.dirname(__file__)
    data_sources = OSMDataManagerV2.get_default_data_sources(project_root)
    
    print("📁 Sources de données:")
    for source_name, file_path in data_sources.items():
        exists = "✅" if os.path.exists(file_path) else "❌"
        print(f"   {exists} {source_name}: {os.path.basename(file_path)}")
    print()
    
    # 3. Vérifier si un cache existe
    cache_available = manager.is_cache_available(data_sources)
    print(f"💾 Cache disponible: {'✅' if cache_available else '❌'}")
    
    if cache_available:
        cache_info = manager.get_cache_info()
        if cache_info:
            print("📊 Informations du cache:")
            cache_info.print_summary()
            print()
    
    # 4. Premier test : construction complète
    print("🚀 TEST 1: Construction/chargement des données")
    start_time = time.time()
    
    success = manager.initialize(data_sources, force_rebuild=False)
    
    init_time = time.time() - start_time
    print(f"⏱️ Temps d'initialisation: {init_time:.2f}s")
    
    if not success:
        print("❌ Échec de l'initialisation")
        return False
    
    # 5. Afficher les statistiques
    stats = manager.get_data_stats()
    print(f"\n📊 Statistiques après correction (distance 2m):")
    for key, value in stats.items():
        print(f"   • {key}: {value}")
    
    # 6. Rechercher les liens contenant way/657897788
    print(f"\n🔍 Recherche des liens contenant way/657897788...")
    target_segment = "way/657897788"
    found_links = find_links_with_segment(manager, target_segment)
    
    if found_links:
        print(f"✅ Segment trouvé dans {len(found_links)} lien(s):")
        for link in found_links:
            print(f"\n   📍 Lien: {link.link_id}")
            print(f"      Type: {link.link_type.value}")
            print(f"      Segments: {link.get_segment_count()}")
            if link.has_toll():
                print(f"      Péage: {link.associated_toll.display_name}")
                print(f"      Distance péage: {link.toll_distance_meters:.1f}m")
            
            # Afficher la séquence des segments
            segment_ids = [segment.way_id for segment in link.segments]
            target_position = segment_ids.index(target_segment)
            print(f"      Position de {target_segment}: {target_position}")
            
            # Afficher un contexte autour du segment cible
            start_idx = max(0, target_position - 2)
            end_idx = min(len(segment_ids), target_position + 3)
            context_segments = segment_ids[start_idx:end_idx]
            
            print(f"      Contexte: {' → '.join(context_segments)}")
            if target_position > 2:
                print(f"      (... {target_position - 2} segments avant)")
            if target_position < len(segment_ids) - 3:
                print(f"      (... {len(segment_ids) - target_position - 3} segments après)")
            
            # Afficher les segments attendus s'ils sont présents
            expected_segments = ["way/126357480", "way/1298540619", "way/1298540620"]
            found_expected = []
            for expected in expected_segments:
                if expected in segment_ids:
                    pos = segment_ids.index(expected)
                    found_expected.append(f"{expected} (pos {pos})")
            
            if found_expected:
                print(f"      Segments attendus trouvés: {', '.join(found_expected)}")
    else:
        print("❌ Segment non trouvé")
    
    # 7. Test de rechargement depuis le cache
    print(f"\n🚀 TEST 2: Rechargement depuis le cache")
    manager2 = OSMDataManagerV2(cache_dir="osm_cache_v2_test")
    
    start_time = time.time()
    success2 = manager2.initialize(data_sources, force_rebuild=False)
    reload_time = time.time() - start_time
    
    if success2:
        print(f"✅ Rechargement réussi en {reload_time:.2f}s")
        if reload_time < init_time:
            speedup = init_time / reload_time
            print(f"🚀 Accélération: {speedup:.1f}x plus rapide")
            print(f"⏱️ Temps économisé: {init_time - reload_time:.2f}s")
    
    print("\n✅ Test de sérialisation terminé!")
    return True


def find_links_with_segment(manager, target_segment):
    """Trouve tous les liens contenant un segment spécifique."""
    all_links = manager.get_all_complete_links()
    found_links = []
    
    for link in all_links:
        segment_ids = [segment.way_id for segment in link.segments]
        if target_segment in segment_ids:
            found_links.append(link)
    
    return found_links


def find_target_sequence(manager, target_sequence):
    """Trouve le lien contenant la séquence cible."""
    all_links = manager.get_all_complete_links()
    
    for link in all_links:
        segment_ids = [segment.way_id for segment in link.segments]
        
        # Vérifier si la séquence est contenue
        if contains_sequence(segment_ids, target_sequence):
            return link
    
    return None


def contains_sequence(haystack, needle):
    """Vérifie si needle est une sous-séquence de haystack."""
    if len(needle) > len(haystack):
        return False
    
    for i in range(len(haystack) - len(needle) + 1):
        if haystack[i:i + len(needle)] == needle:
            return True
    return False


if __name__ == "__main__":
    test_with_serialization()
