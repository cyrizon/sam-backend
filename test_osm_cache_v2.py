#!/usr/bin/env python3
"""
Test OSM Cache V2
----------------

Script de test pour la nouvelle architecture de cache OSM multi-sources.
"""

import os
import sys
import time

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.cache.v2 import OSMDataManagerV2


def test_osm_cache_v2():
    """Test complet du système OSM V2."""
    print("🧪 Test OSM Cache V2\n")
    
    # 1. Initialiser le gestionnaire
    manager = OSMDataManagerV2()
    
    # 2. Définir les sources de données
    project_root = os.path.dirname(__file__)  # Répertoire du script (sam-backend)
    data_sources = OSMDataManagerV2.get_default_data_sources(project_root)
    
    print("📁 Sources de données:")
    for source_name, file_path in data_sources.items():
        exists = "✅" if os.path.exists(file_path) else "❌"
        print(f"   {exists} {source_name}: {file_path}")
    print()
    
    # 3. Initialiser avec mesure du temps
    start_time = time.time()
    success = manager.initialize(data_sources)
    init_time = time.time() - start_time
    
    if not success:
        print("❌ Échec de l'initialisation")
        return False
    
    print(f"⏱️ Temps d'initialisation: {init_time:.2f}s\n")
    
    # 4. Afficher les statistiques
    stats = manager.get_data_stats()
    print("📊 Statistiques détaillées:")
    for key, value in stats.items():
        print(f"   • {key}: {value}")
    print()
    
    # 5. Tests d'API
    print("🔍 Tests d'API:")
    
    # Test toll booths
    toll_booths = manager.get_toll_booths()
    print(f"   • get_toll_booths(): {len(toll_booths)} péages")
    if toll_booths:
        first_toll = toll_booths[0]
        print(f"     Exemple: {first_toll.display_name} @ {first_toll.coordinates}")
    
    # Test complete links
    entry_links = manager.get_complete_entry_links()
    exit_links = manager.get_complete_exit_links()
    all_links = manager.get_all_complete_links()
    print(f"   • get_complete_entry_links(): {len(entry_links)} liens")
    print(f"   • get_complete_exit_links(): {len(exit_links)} liens")
    print(f"   • get_all_complete_links(): {len(all_links)} liens")
    
    # Test links with tolls
    links_with_tolls = manager.get_links_with_tolls()
    print(f"   • get_links_with_tolls(): {len(links_with_tolls)} liens avec péages")
    
    if links_with_tolls:
        toll_link = links_with_tolls[0]
        print(f"     Exemple: {toll_link.link_id} avec péage {toll_link.associated_toll.display_name}")
        print(f"     Distance: {toll_link.toll_distance_meters:.1f}m")
        print(f"     Segments: {toll_link.get_segment_count()}")
    
    print("\n✅ Test OSM Cache V2 terminé avec succès!")
    return True


if __name__ == "__main__":
    test_osm_cache_v2()
