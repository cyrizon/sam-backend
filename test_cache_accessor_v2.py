"""
Test Cache Accessor V2
======================

Test du nouvel accesseur de cache V2 pour route optimization.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.services.toll.route_optimization.utils.cache_accessor import CacheAccessor


def test_cache_v2_integration():
    """Test d'intégration du cache V2."""
    
    print("🧪 Test du cache accessor V2")
    print("=" * 50)
    
    # Test 1: Vérification disponibilité (force l'initialisation)
    print("\n1️⃣ Test disponibilité du cache...")
    # Force l'initialisation en appelant _ensure_initialized
    CacheAccessor._ensure_initialized()
    is_available = CacheAccessor.is_cache_available()
    print(f"   Cache disponible: {is_available}")
    
    if not is_available:
        print("❌ Cache non disponible, arrêt du test")
        return
    
    # Test 2: Statistiques générales
    print("\n2️⃣ Test statistiques du cache...")
    stats = CacheAccessor.get_cache_stats()
    print(f"   • Stations de péage: {stats['toll_stations']}")
    print(f"   • Liens complets: {stats['complete_links']}")
    print(f"   • Liens avec péages: {stats['links_with_tolls']}")
    print(f"   • Liens d'entrée: {stats['entry_links']}")
    print(f"   • Liens de sortie: {stats['exit_links']}")
    
    # Test 3: Péages par type
    if 'toll_types' in stats:
        print(f"   • Péages ouverts: {stats['toll_types']['open_tolls']}")
        print(f"   • Péages fermés: {stats['toll_types']['closed_tolls']}")
    
    # Test 4: Opérateurs principaux
    if 'operators' in stats:
        print(f"\n🏢 Top 5 opérateurs:")
        sorted_ops = sorted(stats['operators'].items(), key=lambda x: x[1], reverse=True)
        for op, count in sorted_ops[:5]:
            print(f"   • {op}: {count} liens")
    
    # Test 5: Récupération des données
    print("\n3️⃣ Test récupération des données...")
    
    # Péages
    toll_stations = CacheAccessor.get_toll_stations()
    print(f"   • Récupéré {len(toll_stations)} stations de péage")
    
    # Liens avec péages
    links_with_tolls = CacheAccessor.get_links_with_tolls()
    print(f"   • Récupéré {len(links_with_tolls)} liens avec péages")
    
    # Test 6: Exemples de liens avec péages
    if links_with_tolls:
        print(f"\n4️⃣ Exemples de liens avec péages:")
        for i, link in enumerate(links_with_tolls[:3]):  # 3 premiers
            print(f"   {i+1}. {link.link_id}")
            print(f"      • Type: {link.link_type.value}")
            print(f"      • Segments: {len(link.segments)}")
            print(f"      • Péage: {link.associated_toll.name}")
            print(f"      • Opérateur: {link.associated_toll.operator}")
            print(f"      • Distance: {link.toll_distance_meters:.2f}m")
            print(f"      • Type péage: {'Ouvert' if link.associated_toll.is_open_toll else 'Fermé'}")
    
    # Test 7: Filtrage par type de péage
    print(f"\n5️⃣ Test filtrage...")
    open_tolls = CacheAccessor.get_links_by_toll_type("O")
    closed_tolls = CacheAccessor.get_links_by_toll_type("F")
    print(f"   • Liens avec péages ouverts: {len(open_tolls)}")
    print(f"   • Liens avec péages fermés: {len(closed_tolls)}")
    
    # Test 8: Filtrage par opérateur
    if stats.get('operators'):
        top_operator = max(stats['operators'].items(), key=lambda x: x[1])[0]
        operator_links = CacheAccessor.get_links_by_operator(top_operator)
        print(f"   • Liens avec opérateur '{top_operator}': {len(operator_links)}")
    
    # Test 9: Calcul de coût (si possible)
    print(f"\n6️⃣ Test calcul de coûts...")
    if links_with_tolls:
        sample_link = links_with_tolls[0]
        cost = CacheAccessor.calculate_toll_cost(sample_link, "1")
        if cost is not None:
            print(f"   • Coût exemple ({sample_link.associated_toll.name}): {cost:.2f}€")
        else:
            print(f"   • Calcul coût non disponible pour {sample_link.associated_toll.name}")
    
    print(f"\n✅ Test du cache accessor V2 terminé!")


def test_cache_performance():
    """Test rapide de performance du cache."""
    
    print("\n⚡ Test de performance...")
    
    import time
    
    # Test vitesse d'accès
    start = time.time()
    
    # 10 accès répétés
    for _ in range(10):
        links = CacheAccessor.get_links_with_tolls()
        stats = CacheAccessor.get_cache_stats()
    
    end = time.time()
    
    print(f"   • 10 accès répétés: {(end-start)*1000:.1f}ms")
    print(f"   • Moyenne par accès: {(end-start)*100:.1f}ms")


if __name__ == "__main__":
    print("🚀 Tests du Cache Accessor V2")
    print("=" * 60)
    
    try:
        test_cache_v2_integration()
        test_cache_performance()
        
        print("\n🎉 Tous les tests ont réussi!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
