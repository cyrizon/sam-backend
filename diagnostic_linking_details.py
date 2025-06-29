"""
Diagnostic détaillé de la liaison des segments motorway
"""

import os
import sys

# Ajouter le répertoire src au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cache.v2.managers.v2_cache_manager_with_linking import V2CacheManagerWithLinking


def main():
    """Diagnostic détaillé de la liaison des segments."""
    
    print("🔍 DIAGNOSTIC DÉTAILLÉ DE LA LIAISON DES SEGMENTS")
    print("=" * 60)
    
    # Créer le gestionnaire
    data_dir = "data"
    cache_manager = V2CacheManagerWithLinking(data_dir)
    
    # Forcer la reconstruction pour avoir les détails
    cache_manager.clear_links_cache()
    success = cache_manager.load_all_including_motorway_linking()
    
    if not success:
        print("❌ Échec du chargement")
        return
    
    # Analyser les résultats
    complete_links = cache_manager.get_complete_motorway_links()
    entry_links = cache_manager.get_entry_links()
    exit_links = cache_manager.get_exit_links()
    
    print(f"\n📊 RÉSUMÉ DES LIENS CRÉÉS:")
    print(f"   • Total liens complets: {len(complete_links)}")
    print(f"   • Liens d'entrée: {len(entry_links)}")
    print(f"   • Liens de sortie: {len(exit_links)}")
    
    # Analyser la composition des liens
    print(f"\n🔍 ANALYSE DE LA COMPOSITION DES LIENS:")
    
    # Compter les types de liens
    entry_complex = 0  # Liens avec plusieurs segments
    entry_simple = 0   # Liens avec un seul segment
    exit_complex = 0
    exit_simple = 0
    
    for link in entry_links:
        if len(link.segments) > 1:
            entry_complex += 1
        else:
            entry_simple += 1
    
    for link in exit_links:
        if len(link.segments) > 1:
            exit_complex += 1
        else:
            exit_simple += 1
    
    print(f"📥 ENTRÉES ({len(entry_links)} total):")
    print(f"   • Liens complexes (multi-segments): {entry_complex}")
    print(f"   • Liens simples (1 segment): {entry_simple}")
    
    print(f"📤 SORTIES ({len(exit_links)} total):")
    print(f"   • Liens complexes (multi-segments): {exit_complex}")
    print(f"   • Liens simples (1 segment): {exit_simple}")
    
    # Analyser la taille des liens
    print(f"\n📏 TAILLE MOYENNE DES LIENS:")
    
    if entry_links:
        entry_segments_total = sum(len(link.segments) for link in entry_links)
        entry_avg = entry_segments_total / len(entry_links)
        print(f"   • Entrées: {entry_avg:.1f} segments/lien")
    
    if exit_links:
        exit_segments_total = sum(len(link.segments) for link in exit_links)
        exit_avg = exit_segments_total / len(exit_links)
        print(f"   • Sorties: {exit_avg:.1f} segments/lien")
    
    # Analyser les liens les plus complexes
    print(f"\n🏗️  EXEMPLES DE LIENS COMPLEXES:")
    
    # Top 5 liens d'entrée les plus complexes
    entry_by_size = sorted(entry_links, key=lambda x: len(x.segments), reverse=True)
    print(f"📥 Top 5 liens d'entrée par nombre de segments:")
    for i, link in enumerate(entry_by_size[:5]):
        print(f"   {i+1}. {link.link_id}: {len(link.segments)} segments")
        segment_types = {}
        for seg in link.segments:
            seg_type = seg.link_type.value
            segment_types[seg_type] = segment_types.get(seg_type, 0) + 1
        print(f"      → Composition: {dict(segment_types)}")
    
    # Top 5 liens de sortie les plus complexes
    exit_by_size = sorted(exit_links, key=lambda x: len(x.segments), reverse=True)
    print(f"📤 Top 5 liens de sortie par nombre de segments:")
    for i, link in enumerate(exit_by_size[:5]):
        print(f"   {i+1}. {link.link_id}: {len(link.segments)} segments")
        segment_types = {}
        for seg in link.segments:
            seg_type = seg.link_type.value
            segment_types[seg_type] = segment_types.get(seg_type, 0) + 1
        print(f"      → Composition: {dict(segment_types)}")
    
    # Vérifier les liens avec péages
    links_with_tolls = cache_manager.get_links_with_tolls()
    toll_entries = [link for link in links_with_tolls if link.link_type.value == "entry"]
    toll_exits = [link for link in links_with_tolls if link.link_type.value == "exit"]
    
    print(f"\n🏪 LIENS AVEC PÉAGES:")
    print(f"   • Total liens avec péages: {len(links_with_tolls)}")
    print(f"   • Entrées avec péages: {len(toll_entries)}")
    print(f"   • Sorties avec péages: {len(toll_exits)}")
    
    if len(toll_exits) > 0:
        exit_toll_percentage = (len(toll_exits) / len(exit_links)) * 100
        print(f"   • % sorties avec péages: {exit_toll_percentage:.1f}%")
    
    if len(toll_entries) > 0:
        entry_toll_percentage = (len(toll_entries) / len(entry_links)) * 100
        print(f"   • % entrées avec péages: {entry_toll_percentage:.1f}%")
    
    # Analyser les statistiques de liaison
    linking_stats = cache_manager.get_linking_statistics()
    if linking_stats:
        print(f"\n⚡ EFFICACITÉ DE LIAISON:")
        if 'linking_efficiency' in linking_stats:
            efficiency = linking_stats['linking_efficiency']
            print(f"   • Segments utilisés: {efficiency.get('segments_used', 'N/A')}")
            print(f"   • Pourcentage d'utilisation: {efficiency.get('usage_percentage', 'N/A'):.1f}%")
        
        if 'orphaned_segments' in linking_stats:
            orphans = linking_stats['orphaned_segments']
            print(f"   • Chaînes orphelines: {orphans.get('unused_chains', 'N/A')}")
            print(f"   • Segments individuels orphelins: {orphans.get('individual_segments', 'N/A')}")
    
    print(f"\n✅ Diagnostic détaillé terminé!")


if __name__ == "__main__":
    main()
