"""
Test de correction des coordonnées dupliquées dans CompleteMotorwayLink
"""

import os
import sys

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.cache.v2.models.motorway_link import MotorwayLink
from src.cache.v2.models.complete_motorway_link import CompleteMotorwayLink
from src.cache.v2.models.link_types import LinkType


def test_coordinate_deduplication():
    """Test de déduplication des coordonnées."""
    
    print("🧪 Test de déduplication des coordonnées")
    print("=" * 50)
    
    # Créer des segments avec points de connexion identiques
    segment1 = MotorwayLink(
        way_id="seg1",
        link_type=LinkType.INDETERMINATE,
        coordinates=[
            [4.527926, 45.8761563],
            [4.5274825, 45.8760868],
            [4.5271901, 45.8760632],
            [4.5268484, 45.8760524]
        ],
        properties={}
    )
    
    segment2 = MotorwayLink(
        way_id="seg2",
        link_type=LinkType.INDETERMINATE,
        coordinates=[
            [4.5268484, 45.8760524],  # Même point que la fin de segment1
            [4.5265271, 45.8760619],
            [4.5257314, 45.8761271],
            [4.5253877, 45.8761375]
        ],
        properties={}
    )
    
    segment3 = MotorwayLink(
        way_id="seg3",
        link_type=LinkType.ENTRY,
        coordinates=[
            [4.5253877, 45.8761375],  # Même point que la fin de segment2
            [4.5249933, 45.8761358],
            [4.5246788, 45.8761111],
            [4.5241859, 45.8760724]
        ],
        properties={}
    )
    
    # Créer le lien complet
    complete_link = CompleteMotorwayLink(
        link_id="test_link_123",
        link_type=LinkType.ENTRY,
        segments=[segment1, segment2, segment3],
        destination="Test Destination"
    )
    
    # Tester les coordonnées
    all_coords = complete_link.get_all_coordinates()
    
    print(f"📊 Résultats:")
    print(f"   - Segment 1: {len(segment1.coordinates)} coordonnées")
    print(f"   - Segment 2: {len(segment2.coordinates)} coordonnées")
    print(f"   - Segment 3: {len(segment3.coordinates)} coordonnées")
    print(f"   - Total brut: {len(segment1.coordinates) + len(segment2.coordinates) + len(segment3.coordinates)} coordonnées")
    print(f"   - Total après déduplication: {len(all_coords)} coordonnées")
    
    # Vérifier qu'il n'y a plus de doublons consécutifs
    doublons_found = 0
    for i in range(len(all_coords) - 1):
        if all_coords[i] == all_coords[i + 1]:
            doublons_found += 1
            print(f"⚠️  Doublon trouvé à l'index {i}: {all_coords[i]}")
    
    if doublons_found == 0:
        print("✅ Aucun doublon consécutif trouvé!")
    else:
        print(f"❌ {doublons_found} doublons consécutifs trouvés")
    
    # Afficher quelques coordonnées pour vérification
    print(f"\n📍 Premières coordonnées:")
    for i, coord in enumerate(all_coords[:5]):
        print(f"   {i}: {coord}")
    
    print(f"\n📍 Dernières coordonnées:")
    for i, coord in enumerate(all_coords[-5:]):
        print(f"   {len(all_coords) - 5 + i}: {coord}")
    
    # Test avec segments sans connexion
    print(f"\n🧪 Test avec segments non connectés")
    print("-" * 40)
    
    segment_isolated = MotorwayLink(
        way_id="seg_isolated",
        link_type=LinkType.INDETERMINATE,
        coordinates=[
            [4.6000000, 45.9000000],
            [4.6001000, 45.9001000],
            [4.6002000, 45.9002000]
        ],
        properties={}
    )
    
    complete_link_mixed = CompleteMotorwayLink(
        link_id="test_mixed_123",
        link_type=LinkType.EXIT,
        segments=[segment1, segment_isolated],  # Pas de connexion
        destination="Test Mixed"
    )
    
    mixed_coords = complete_link_mixed.get_all_coordinates()
    print(f"   - Coordonnées segment1: {len(segment1.coordinates)}")
    print(f"   - Coordonnées segment isolé: {len(segment_isolated.coordinates)}")
    print(f"   - Total après traitement: {len(mixed_coords)}")
    print(f"   - Attendu (pas de connexion): {len(segment1.coordinates) + len(segment_isolated.coordinates)}")
    
    if len(mixed_coords) == len(segment1.coordinates) + len(segment_isolated.coordinates):
        print("✅ Segments non connectés traités correctement!")
    else:
        print("❌ Problème avec les segments non connectés")
    
    return doublons_found == 0


def test_with_real_cache():
    """Test avec le cache réel."""
    
    print(f"\n🏗️  Test avec le cache réel")
    print("=" * 40)
    
    try:
        from src.cache.v2.managers.v2_cache_manager_with_linking import V2CacheManagerWithLinking
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, "data")
        cache_dir = "osm_cache_v2_test"
        
        print(f"📂 Chargement du cache depuis: {data_dir}")
        
        cache_manager = V2CacheManagerWithLinking(data_dir, cache_dir)
        success = cache_manager.load_all_including_motorway_linking()
        
        if not success:
            print("❌ Impossible de charger le cache")
            return False
        
        all_links = cache_manager.get_complete_motorway_links()
        
        if not all_links:
            print("⚠️  Aucun lien complet trouvé")
            return False
        
        # Tester les premiers liens
        print(f"📊 Analyse de {min(10, len(all_links))} liens...")
        
        total_doublons = 0
        for i, link in enumerate(all_links[:10]):
            coords = link.get_all_coordinates()
            
            # Compter les doublons consécutifs
            doublons = 0
            for j in range(len(coords) - 1):
                if coords[j] == coords[j + 1]:
                    doublons += 1
            
            total_doublons += doublons
            
            print(f"   Lien {i+1}: {len(coords)} coordonnées, {doublons} doublons consécutifs")
        
        print(f"\n🎯 Résultat: {total_doublons} doublons consécutifs trouvés au total")
        
        if total_doublons == 0:
            print("✅ Correction réussie - Plus de doublons consécutifs!")
        else:
            print(f"⚠️  Il reste {total_doublons} doublons consécutifs")
        
        return total_doublons == 0
        
    except Exception as e:
        print(f"❌ Erreur lors du test avec le cache réel: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Test de correction des coordonnées dupliquées")
    print("=" * 60)
    
    # Test unitaire
    test1_ok = test_coordinate_deduplication()
    
    # Test avec le cache réel
    test2_ok = test_with_real_cache()
    
    print(f"\n🎉 Résultats finaux:")
    print(f"   - Test unitaire: {'✅ RÉUSSI' if test1_ok else '❌ ÉCHEC'}")
    print(f"   - Test cache réel: {'✅ RÉUSSI' if test2_ok else '❌ ÉCHEC'}")
    
    if test1_ok and test2_ok:
        print(f"\n🎯 Correction des coordonnées dupliquées RÉUSSIE!")
    else:
        print(f"\n⚠️  Des problèmes subsistent...")
