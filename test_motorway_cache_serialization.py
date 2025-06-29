"""
Test de la sérialisation des liens motorway V2
----------------------------------------------

Test du système de cache pour éviter de recalculer les liens à chaque démarrage.
"""

import os
import sys
import time

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cache.v2.managers.v2_cache_manager_with_linking import V2CacheManagerWithLinking


def test_cache_serialization():
    """Test complet de la sérialisation du cache."""
    print("🧪 Test de la sérialisation des liens motorway V2")
    print("=" * 55)
    
    data_dir = "data"
    cache_dir = "osm_cache_v2_test"
    
    # Premier chargement (construction des liens)
    print("\n1️⃣  Premier chargement - Construction des liens")
    print("-" * 45)
    
    manager1 = V2CacheManagerWithLinking(data_dir, cache_dir)
    
    start_time = time.time()
    success1 = manager1.load_all_including_motorway_linking()
    build_time = time.time() - start_time
    
    if not success1:
        print("❌ Échec du premier chargement")
        return False
    
    print(f"⏱️  Temps de construction: {build_time:.2f}s")
    print(f"📊 Liens créés: {len(manager1.get_complete_motorway_links())}")
    
    # Vérifier les infos du cache
    cache_info = manager1.get_cache_info()
    if cache_info:
        print(f"💾 Cache créé:")
        print(f"   • Version: {cache_info.get('version', 'N/A')}")
        print(f"   • Liens: {cache_info.get('links_count', 'N/A')}")
        for name, info in cache_info.get('files_info', {}).items():
            print(f"   • {name}: {info['size_mb']} MB")
    
    # Deuxième chargement (depuis le cache)
    print("\n2️⃣  Deuxième chargement - Depuis le cache")
    print("-" * 42)
    
    manager2 = V2CacheManagerWithLinking(data_dir, cache_dir)
    
    start_time = time.time()
    success2 = manager2.load_all_including_motorway_linking()
    cache_time = time.time() - start_time
    
    if not success2:
        print("❌ Échec du deuxième chargement")
        return False
    
    print(f"⏱️  Temps de chargement cache: {cache_time:.2f}s")
    print(f"📊 Liens chargés: {len(manager2.get_complete_motorway_links())}")
    
    # Comparaison des performances
    print(f"\n⚡ Amélioration des performances:")
    if cache_time > 0:
        speedup = build_time / cache_time
        print(f"   • Accélération: {speedup:.1f}x plus rapide")
        print(f"   • Temps économisé: {build_time - cache_time:.2f}s")
    
    # Vérification de la cohérence
    print(f"\n🔍 Vérification de la cohérence:")
    links1 = manager1.get_complete_motorway_links()
    links2 = manager2.get_complete_motorway_links()
    
    if len(links1) == len(links2):
        print(f"   ✅ Nombre de liens identique: {len(links1)}")
    else:
        print(f"   ❌ Nombre de liens différent: {len(links1)} vs {len(links2)}")
        return False
    
    # Vérifier quelques liens spécifiques
    coherent = True
    for i in range(min(5, len(links1))):
        link1 = links1[i]
        link2 = links2[i]
        
        if (link1.link_id == link2.link_id and 
            len(link1.segments) == len(link2.segments) and
            link1.link_type == link2.link_type):
            print(f"   ✅ Lien {i+1} cohérent: {link1.link_id}")
        else:
            print(f"   ❌ Lien {i+1} incohérent")
            coherent = False
    
    if not coherent:
        return False
    
    # Test de suppression du cache
    print(f"\n3️⃣  Test de suppression du cache")
    print("-" * 35)
    
    cache_cleared = manager2.clear_links_cache()
    if cache_cleared:
        print("   ✅ Cache supprimé avec succès")
    else:
        print("   ❌ Échec de la suppression du cache")
        return False
    
    # Test de reconstruction forcée
    print(f"\n4️⃣  Test de reconstruction forcée")
    print("-" * 36)
    
    start_time = time.time()
    rebuild_success = manager2.force_rebuild_links()
    rebuild_time = time.time() - start_time
    
    if rebuild_success:
        print(f"   ✅ Reconstruction réussie en {rebuild_time:.2f}s")
        print(f"   📊 Liens reconstruits: {len(manager2.get_complete_motorway_links())}")
    else:
        print("   ❌ Échec de la reconstruction")
        return False
    
    return True


def test_cache_validation():
    """Test de la validation du cache en cas de modification des fichiers sources."""
    print("\n🔍 Test de validation du cache")
    print("=" * 35)
    
    data_dir = "data"
    cache_dir = "osm_cache_v2_test"
    
    manager = V2CacheManagerWithLinking(data_dir, cache_dir)
    
    # Vérifier la validité du cache
    source_files = manager._get_source_files_paths()
    is_valid = manager.links_serializer.is_cache_valid(source_files)
    
    print(f"Cache valide: {'✅' if is_valid else '❌'}")
    
    if is_valid:
        print("Les fichiers sources n'ont pas été modifiés depuis la création du cache")
    else:
        print("Les fichiers sources ont été modifiés ou le cache est invalide")
    
    return True


if __name__ == "__main__":
    print("🚀 Test de la sérialisation des liens motorway V2")
    
    # Test principal
    success = test_cache_serialization()
    
    if success:
        print("\n✅ Tous les tests de sérialisation ont réussi!")
        
        # Test de validation
        test_cache_validation()
    else:
        print("\n❌ Échec des tests de sérialisation!")
