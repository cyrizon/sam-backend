"""
Test de l'association des péages aux liens motorway complets
"""

import pytest
import os
import sys

# Ajouter le répertoire src au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cache.v2.managers.v2_cache_manager_with_linking import V2CacheManagerWithLinking
from src.cache.v2.services.toll_association_service import TollAssociationService
from src.cache.v2.models.complete_motorway_link import CompleteMotorwayLink
from src.cache.v2.models.motorway_link import MotorwayLink
from src.cache.v2.models.toll_booth_station import TollBoothStation
from src.cache.v2.models.link_types import LinkType


def test_toll_association_integration():
    """Test d'intégration de l'association des péages."""
    
    print("🧪 Test d'intégration de l'association des péages")
    
    # Créer le gestionnaire
    data_dir = "data"
    cache_manager = V2CacheManagerWithLinking(data_dir)
    
    # Charger toutes les données y compris la liaison
    success = cache_manager.load_all_including_motorway_linking()
    
    if not success:
        print("⚠️  Impossible de charger les données, test ignoré")
        return
    
    # Vérifier qu'on a des liens complets
    complete_links = cache_manager.get_complete_motorway_links()
    assert len(complete_links) > 0, "Aucun lien complet trouvé"
    
    print(f"✅ Liens complets chargés: {len(complete_links)}")
    
    # Vérifier qu'on a des péages
    toll_booths = cache_manager.toll_booths
    assert len(toll_booths) > 0, "Aucun péage trouvé"
    
    print(f"✅ Péages chargés: {len(toll_booths)}")
    
    # Vérifier les associations
    links_with_tolls = cache_manager.get_links_with_tolls()
    print(f"📊 Liens avec péages: {len(links_with_tolls)}")
    
    if links_with_tolls:
        # Tester les filtres
        open_tolls = cache_manager.get_links_by_toll_type("O")
        closed_tolls = cache_manager.get_links_by_toll_type("F")
        
        print(f"   • Péages ouverts: {len(open_tolls)}")
        print(f"   • Péages fermés: {len(closed_tolls)}")
        
        # Tester les opérateurs
        if links_with_tolls:
            sample_operator = links_with_tolls[0].associated_toll.operator
            operator_links = cache_manager.get_links_by_operator(sample_operator)
            print(f"   • Liens avec opérateur '{sample_operator}': {len(operator_links)}")
        
        # Vérifier les distances
        for link in links_with_tolls[:3]:  # Premiers exemples
            assert link.has_toll(), "Le lien devrait avoir un péage"
            assert link.toll_distance_meters is not None, "La distance devrait être définie"
            assert link.toll_distance_meters <= 2.0, f"Distance trop grande: {link.toll_distance_meters}m"
            
            print(f"   • Lien {link.link_id}: péage à {link.toll_distance_meters:.2f}m ({link.associated_toll.operator})")
    
    # Vérifier les statistiques
    stats = cache_manager.get_toll_association_statistics()
    if stats:
        assert stats["total_links"] == len(complete_links)
        assert stats["links_with_tolls"] == len(links_with_tolls)
        print(f"✅ Statistiques cohérentes")
    
    print("🎉 Test d'intégration de l'association des péages réussi!")


def test_toll_association_service_standalone():
    """Test du service d'association en isolation."""
    
    print("🧪 Test du service d'association en isolation")
    
    # Créer des données de test
    # Créer un lien simple
    segment = MotorwayLink(
        way_id="test_way",
        link_type=LinkType.ENTRY,
        coordinates=[[2.0, 46.0], [2.001, 46.001]],  # ~111m
        properties={}
    )
    
    complete_link = CompleteMotorwayLink(
        link_id="test_link_1",
        link_type=LinkType.ENTRY,
        segments=[segment]
    )
    
    # Créer des péages de test
    # Péage proche (< 2m) - même coordonnées que le début du segment
    close_toll = TollBoothStation(
        osm_id="toll_1",
        name="Péage Test Proche",
        coordinates=[2.0, 46.0],  # Exactement au début du segment
        operator="TEST",
        operator_ref=None,
        highway_ref=None,
        properties={},
        type="O"
    )
    
    # Péage loin (> 2m)
    far_toll = TollBoothStation(
        osm_id="toll_2",
        name="Péage Test Loin",
        coordinates=[2.1, 46.1],  # ~15km
        operator="TEST",
        operator_ref=None,
        highway_ref=None,
        properties={},
        type="O"
    )
    
    # Tester l'association
    service = TollAssociationService(max_distance_m=2.0)
    
    # Debug: vérifier les distances avant l'association
    print("🔍 Debug distances:")
    link_coords = complete_link.get_all_coordinates()
    print(f"   • Coordonnées du lien: {link_coords}")
    
    for toll in [close_toll, far_toll]:
        print(f"   • Péage {toll.osm_id} à {toll.coordinates}")
        min_dist = float('inf')
        for coord in link_coords:
            from src.cache.v2.linking.coordinate_matcher import calculate_distance_meters
            dist = calculate_distance_meters(coord, toll.coordinates)
            min_dist = min(min_dist, dist)
        print(f"     → Distance minimale: {min_dist:.2f}m")
    
    stats = service.associate_tolls_to_links([complete_link], [close_toll, far_toll])
    
    # Vérifications
    assert stats["total_links"] == 1
    assert stats["total_tolls"] == 2
    assert stats["links_with_tolls"] == 1  # Seul le péage proche devrait être associé
    assert stats["associations_made"] == 1
    
    # Vérifier l'association
    assert complete_link.has_toll()
    assert complete_link.associated_toll == close_toll
    assert complete_link.toll_distance_meters < 2.0
    
    print(f"✅ Association correcte: distance = {complete_link.toll_distance_meters:.2f}m")
    
    print("🎉 Test du service d'association réussi!")


if __name__ == "__main__":
    print("🚀 Tests d'association des péages")
    print("=" * 50)
    
    try:
        test_toll_association_service_standalone()
        print()
        test_toll_association_integration()
        
        print("\n✅ Tous les tests d'association des péages ont réussi!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
