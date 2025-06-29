"""
Test du système de liaison de segments motorway V2
--------------------------------------------------

Test complet du nouveau système de liaison modulaire.
"""

import os
import sys

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cache.v2.managers.v2_cache_manager_with_linking import V2CacheManagerWithLinking


def test_complete_motorway_linking_system():
    """Test complet du système de liaison motorway."""
    print("🧪 Test du système de liaison de segments motorway V2")
    print("=" * 60)
    
    # Initialiser le gestionnaire
    data_dir = "data"
    cache_dir = "osm_cache_v2_test"
    
    manager = V2CacheManagerWithLinking(data_dir, cache_dir)
    
    # Test de chargement complet
    print("\n1️⃣  Test de chargement complet...")
    success = manager.load_all_including_motorway_linking()
    
    if not success:
        print("❌ Échec du chargement")
        return False
    
    # Afficher le résumé
    print("\n2️⃣  Résumé du gestionnaire...")
    summary = manager.get_extended_summary()
    print_summary(summary)
    
    # Test des fonctionnalités de liaison
    print("\n3️⃣  Test des fonctionnalités de liaison...")
    test_linking_functions(manager)
    
    # Test d'export
    print("\n4️⃣  Test d'export GeoJSON...")
    export_path = os.path.join(cache_dir, "complete_motorway_links.geojson")
    export_success = manager.export_links_to_geojson(export_path)
    
    if export_success:
        print(f"✅ Export réussi vers: {export_path}")
    else:
        print("❌ Échec de l'export")
    
    # Test de reconstruction avec distance différente
    print("\n5️⃣  Test de reconstruction avec distance 5m...")
    rebuild_success = manager.rebuild_links(max_distance_m=5.0)
    
    if rebuild_success:
        print("✅ Reconstruction réussie")
        new_summary = manager.get_extended_summary()
        print(f"   Nouveaux liens créés: {new_summary['motorway_linking']['links_built']['total_links']}")
    else:
        print("❌ Échec de la reconstruction")
    
    print("\n✅ Test complet terminé!")
    return True


def print_summary(summary):
    """Affiche le résumé de manière lisible."""
    print("📊 RÉSUMÉ DU GESTIONNAIRE V2 AVEC LIAISON")
    print("-" * 40)
    
    # Données de base
    print(f"État chargé: {summary['loaded']}")
    print(f"Toll booths: {summary['toll_booths_count']}")
    print(f"Péages ouverts: {summary['open_tolls_count']}")
    print(f"Péages fermés: {summary['closed_tolls_count']}")
    print(f"Opérateurs: {summary['operators_count']}")
    
    # Données de liaison
    if 'motorway_linking' in summary:
        linking = summary['motorway_linking']
        
        if 'segments_loaded' in linking:
            segments = linking['segments_loaded']
            print(f"\n🛣️  Segments motorway:")
            print(f"   Entrées: {segments['entries']}")
            print(f"   Sorties: {segments['exits']}")
            print(f"   Indéterminés: {segments['indeterminates']}")
            print(f"   Total: {segments['total']}")
        
        if 'links_built' in linking:
            links = linking['links_built']
            print(f"\n🔗 Liens construits:")
            print(f"   Liens d'entrée: {links['entry_links']}")
            print(f"   Liens de sortie: {links['exit_links']}")
            print(f"   Total: {links['total_links']}")
        
        if 'linking_stats' in linking and linking['linking_stats']:
            stats = linking['linking_stats']
            print(f"\n📈 Statistiques de liaison:")
            
            if 'linking_efficiency' in stats:
                eff = stats['linking_efficiency']
                print(f"   Efficacité: {eff['usage_percentage']}%")
                print(f"   Segments utilisés: {eff['segments_in_complete_links']}")
            
            if 'orphaned' in stats:
                orphaned = stats['orphaned']
                print(f"   Chaînes orphelines: {orphaned['unused_chains']}")
                print(f"   Segments orphelins: {orphaned['orphaned_segments']}")


def test_linking_functions(manager):
    """Test les fonctionnalités spécifiques de liaison."""
    
    # Récupérer tous les liens
    all_links = manager.get_complete_motorway_links()
    entry_links = manager.get_entry_links()
    exit_links = manager.get_exit_links()
    
    print(f"   Total liens: {len(all_links)}")
    print(f"   Liens d'entrée: {len(entry_links)}")
    print(f"   Liens de sortie: {len(exit_links)}")
    
    # Test de recherche par ID
    if all_links:
        first_link = all_links[0]
        found_link = manager.get_link_by_id(first_link.link_id)
        if found_link:
            print(f"   ✅ Recherche par ID réussie: {first_link.link_id}")
        else:
            print(f"   ❌ Recherche par ID échouée")
        
        # Test de recherche par way_id
        if first_link.segments:
            way_id = first_link.segments[0].way_id
            links_with_way = manager.get_links_containing_way_id(way_id)
            print(f"   ✅ Liens contenant {way_id}: {len(links_with_way)}")
    
    # Afficher quelques détails sur les liens
    if len(all_links) > 0:
        print(f"\n   📋 Détails du premier lien:")
        link = all_links[0]
        print(f"      ID: {link.link_id}")
        print(f"      Type: {link.link_type.value}")
        print(f"      Segments: {link.get_segment_count()}")
        print(f"      Destination: {link.destination or 'N/A'}")


def test_coordinate_matching():
    """Test unitaire des fonctions de matching de coordonnées."""
    from src.cache.v2.linking.coordinate_matcher import (
        are_coordinates_equal, 
        calculate_distance_meters, 
        are_segments_linkable
    )
    
    print("\n🧪 Test des fonctions de matching de coordonnées")
    print("-" * 45)
    
    # Test égalité exacte
    coord1 = [2.3522, 48.8566]  # Paris
    coord2 = [2.3522, 48.8566]  # Paris (identique)
    coord3 = [2.3523, 48.8567]  # Paris (légèrement différent)
    
    print(f"   Égalité exacte: {are_coordinates_equal(coord1, coord2)}")  # True
    print(f"   Égalité approximative: {are_coordinates_equal(coord1, coord3)}")  # False
    
    # Test calcul de distance
    distance = calculate_distance_meters(coord1, coord3)
    print(f"   Distance Paris: {distance:.2f}m")
    
    # Test de liaison de segments
    can_link, reason = are_segments_linkable(coord1, coord3, max_distance_m=200.0)
    print(f"   Peut lier (200m): {can_link} - {reason}")


def test_chain_building():
    """Test unitaire du constructeur de chaînes."""
    from src.cache.v2.linking.segment_chain_builder import SegmentChainBuilder
    from src.cache.v2.models.motorway_link import MotorwayLink
    from src.cache.v2.models.link_types import LinkType
    
    print("\n🧪 Test du constructeur de chaînes")
    print("-" * 35)
    
    # Créer des segments de test
    segments = [
        MotorwayLink(
            way_id="seg1",
            link_type=LinkType.INDETERMINATE,
            coordinates=[[2.0, 48.0], [2.1, 48.1]],
            properties={}
        ),
        MotorwayLink(
            way_id="seg2",
            link_type=LinkType.INDETERMINATE,
            coordinates=[[2.1, 48.1], [2.2, 48.2]],  # Connecté à seg1
            properties={}
        ),
        MotorwayLink(
            way_id="seg3",
            link_type=LinkType.INDETERMINATE,
            coordinates=[[3.0, 49.0], [3.1, 49.1]],  # Isolé
            properties={}
        )
    ]
    
    builder = SegmentChainBuilder()
    result = builder.build_chains(segments)
    
    stats = result.get_stats()
    print(f"   Chaînes créées: {stats['chains_count']}")
    print(f"   Segments chaînés: {stats['total_chained_segments']}")
    print(f"   Segments orphelins: {stats['orphaned_segments']}")


if __name__ == "__main__":
    print("🚀 Démarrage des tests du système de liaison motorway V2")
    
    # Tests unitaires
    test_coordinate_matching()
    test_chain_building()
    
    # Test complet du système
    test_complete_motorway_linking_system()
