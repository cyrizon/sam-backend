"""
Script de diagnostic et test de l'association des péages
"""

import os
import sys

# Ajouter le répertoire src au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cache.v2.managers.v2_cache_manager_with_linking import V2CacheManagerWithLinking


def main():
    """Diagnostic de l'association des péages."""
    
    print("🔍 DIAGNOSTIC DE L'ASSOCIATION DES PÉAGES")
    print("=" * 50)
    
    # Créer le gestionnaire
    data_dir = "data"
    cache_manager = V2CacheManagerWithLinking(data_dir)
    
    # Option 1: Forcer la reconstruction complète
    print("\n🔄 Reconstruction forcée des liens (avec nouvelle association)...")
    
    # Supprimer le cache pour forcer la reconstruction
    cache_manager.clear_links_cache()
    
    # Charger avec reconstruction
    success = cache_manager.load_all_including_motorway_linking()
    
    if not success:
        print("❌ Échec du chargement")
        return
    
    # Analyser les résultats
    complete_links = cache_manager.get_complete_motorway_links()
    links_with_tolls = cache_manager.get_links_with_tolls()
    
    print(f"\n📊 RÉSULTATS:")
    print(f"   • Total liens: {len(complete_links)}")
    print(f"   • Liens avec péages: {len(links_with_tolls)}")
    
    if len(links_with_tolls) > 0:
        percentage = (len(links_with_tolls) / len(complete_links)) * 100
        print(f"   • Couverture: {percentage:.1f}%")
        
        # Analyser quelques exemples
        print(f"\n🔍 Exemples de liens avec péages:")
        for i, link in enumerate(links_with_tolls[:5]):  # 5 premiers
            print(f"   {i+1}. Lien {link.link_id}")
            print(f"      • Type: {link.link_type.value}")
            print(f"      • Péage: {link.associated_toll.name} ({link.associated_toll.operator})")
            print(f"      • Distance: {link.toll_distance_meters:.2f}m")
            print(f"      • Type péage: {'Ouvert' if link.associated_toll.is_open_toll else 'Fermé'}")
        
        # Statistiques par opérateur
        print(f"\n🏢 Répartition par opérateurs:")
        operator_stats = {}
        for link in links_with_tolls:
            op = link.associated_toll.operator
            operator_stats[op] = operator_stats.get(op, 0) + 1
        
        for op, count in sorted(operator_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   • {op}: {count} liens")
        
        # Statistiques par type
        open_count = len(cache_manager.get_links_by_toll_type("O"))
        closed_count = len(cache_manager.get_links_by_toll_type("F"))
        print(f"\n🏪 Types de péages:")
        print(f"   • Péages ouverts: {open_count}")
        print(f"   • Péages fermés: {closed_count}")
        
        # Distribution des distances
        distances = [link.toll_distance_meters for link in links_with_tolls if link.toll_distance_meters is not None]
        if distances:
            print(f"\n📏 Distances d'association:")
            print(f"   • Moyenne: {sum(distances)/len(distances):.2f}m")
            print(f"   • Min: {min(distances):.2f}m")
            print(f"   • Max: {max(distances):.2f}m")
    
    else:
        print(f"\n⚠️  Aucun péage associé trouvé!")
        print(f"   Cela peut être dû à:")
        print(f"   • Distance seuil trop faible (actuellement 2.0m)")
        print(f"   • Coordonnées des péages trop éloignées des segments")
        print(f"   • Problème dans l'algorithme d'association")
        
        # Tester avec une distance plus grande
        print(f"\n🔍 Test avec distance élargie (50m)...")
        cache_manager.toll_association_service.max_distance_m = 50.0
        
        # Re-essayer l'association
        from src.cache.v2.services.toll_association_service import TollAssociationService
        test_service = TollAssociationService(max_distance_m=50.0)
        test_stats = test_service.associate_tolls_to_links(complete_links, cache_manager.toll_booths)
        
        print(f"   → Avec 50m: {test_stats['links_with_tolls']} liens avec péages")
        
        if test_stats['links_with_tolls'] > 0:
            print(f"   → Distance moyenne: {test_stats['average_distance']:.2f}m")
            print(f"   💡 Suggestion: augmenter la distance seuil à ~{test_stats['average_distance']*1.2:.0f}m")
    
    # Informations sur le cache
    cache_info = cache_manager.get_cache_info()
    if cache_info:
        print(f"\n💾 Informations du cache:")
        print(f"   • Créé: {cache_info.get('created_at', 'N/A')}")
        print(f"   • Version: {cache_info.get('version', 'N/A')}")
        print(f"   • Liens: {cache_info.get('links_count', 'N/A')}")
    
    print(f"\n✅ Diagnostic terminé!")


if __name__ == "__main__":
    main()
