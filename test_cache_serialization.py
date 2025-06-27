#!/usr/bin/env python3
"""
Script de test et démonstration du cache sérialisé OSM.

Ce script permet de tester les performances du nouveau système de cache
avec sérialisation et compression.
"""

import os
import sys
import time

# Ajouter src au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cache.cached_osm_manager import CachedOSMDataManager
from src.cache.serialization.compression_utils import CompressionType


def test_cache_performance():
    """Test les performances du cache sérialisé."""
    
    print("🧪 TEST DU CACHE SÉRIALISÉ OSM")
    print("=" * 50)
    
    # Configuration
    osm_file = "data/osm_export_toll.geojson"
    cache_dir = "osm_cache"
    
    if not os.path.exists(osm_file):
        print(f"❌ Fichier OSM non trouvé: {osm_file}")
        return False
    
    # Créer le gestionnaire de cache
    cached_manager = CachedOSMDataManager(cache_dir)
    
    print(f"\n📁 Configuration:")
    print(f"   - Fichier OSM: {osm_file}")
    print(f"   - Dossier cache: {cache_dir}")
    print(f"   - Taille fichier OSM: {os.path.getsize(osm_file) / 1024 / 1024:.1f} MB")
    
    # Test 1: Premier chargement (création du cache)
    print(f"\n🚀 TEST 1: Premier chargement (création du cache)")
    print("-" * 50)
    
    start_time = time.time()
    success = cached_manager.load_osm_data_with_cache(osm_file, force_reload=True)
    first_load_time = time.time() - start_time
    
    if not success:
        print("❌ Échec du premier chargement")
        return False
    
    print(f"✅ Premier chargement réussi en {first_load_time:.2f}s")
    
    # Afficher les statistiques des données chargées
    if cached_manager.osm_parser:
        parser = cached_manager.osm_parser
        print(f"   📊 Données chargées:")
        print(f"      - Péages: {len(parser.toll_stations)}")
        print(f"      - Junctions: {len(parser.motorway_junctions)}")
        print(f"      - Links: {len(parser.motorway_links)}")
    
    # Afficher info cache
    cache_info = cached_manager.get_cache_info()
    if cache_info:
        cache_info.print_summary()
    
    # Test 2: Chargement depuis le cache
    print(f"\n🚀 TEST 2: Chargement depuis le cache")
    print("-" * 50)
    
    # Créer un nouveau gestionnaire pour simuler un redémarrage
    cached_manager2 = CachedOSMDataManager(cache_dir)
    
    start_time = time.time()
    success = cached_manager2.load_osm_data_with_cache(osm_file, force_reload=False)
    cached_load_time = time.time() - start_time
    
    if not success:
        print("❌ Échec du chargement depuis le cache")
        return False
    
    print(f"✅ Chargement depuis cache réussi en {cached_load_time:.2f}s")
    
    # Calculer l'amélioration de performance
    if cached_load_time > 0:
        speedup = first_load_time / cached_load_time
        print(f"🚀 Accélération: {speedup:.1f}x plus rapide")
        print(f"⏱️ Temps économisé: {first_load_time - cached_load_time:.2f}s")
    
    # Test 3: Benchmark des méthodes de compression
    print(f"\n🚀 TEST 3: Benchmark des méthodes de compression")
    print("-" * 50)
    
    try:
        benchmark_results = cached_manager.benchmark_cache(osm_file)
        
        print(f"\n🏆 Résultats du benchmark:")
        for method, results in benchmark_results.get('performance_results', {}).items():
            if 'error' not in results:
                total_time = results['save_time_s'] + results['load_time_s']
                print(f"   {method.upper()}: "
                      f"Total {total_time:.2f}s "
                      f"(Save: {results['save_time_s']:.2f}s, Load: {results['load_time_s']:.2f}s), "
                      f"Taille: {results['cache_size_mb']:.1f} MB")
        
    except Exception as e:
        print(f"⚠️ Erreur benchmark: {e}")
    
    print(f"\n✅ Tests terminés avec succès!")
    return True


def clean_cache():
    """Nettoie le cache pour les tests."""
    cache_dir = "osm_cache"
    cached_manager = CachedOSMDataManager(cache_dir)
    
    print("🧹 Nettoyage du cache...")
    success = cached_manager.clear_cache()
    
    if success:
        print("✅ Cache nettoyé")
    else:
        print("⚠️ Erreur nettoyage cache")
    
    return success


def main():
    """Fonction principale."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test du cache sérialisé OSM")
    parser.add_argument('--clean', action='store_true', help='Nettoyer le cache avant les tests')
    parser.add_argument('--benchmark-only', action='store_true', help='Lancer seulement le benchmark')
    
    args = parser.parse_args()
    
    if args.clean:
        clean_cache()
        print()
    
    if args.benchmark_only:
        # Chargement rapide puis benchmark
        osm_file = "data/osm_export_toll.geojson"
        cached_manager = CachedOSMDataManager("osm_cache")
        
        print("📊 Chargement des données pour benchmark...")
        success = cached_manager.load_osm_data_with_cache(osm_file)
        
        if success:
            print("🏁 Lancement du benchmark...")
            cached_manager.benchmark_cache(osm_file)
        else:
            print("❌ Impossible de charger les données")
    else:
        test_cache_performance()


if __name__ == "__main__":
    main()
