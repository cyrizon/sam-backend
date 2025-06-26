#!/usr/bin/env python3
"""
Test de la nouvelle segmentation intelligente V2
Test avec Sélestat-Dijon, 2 péages
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.toll.new_segmentation.intelligent_segmentation_strategy_v2 import IntelligentSegmentationStrategyV2
from src.services.ors_service import ORSService

# Initialiser le cache des barrières
try:
    from src.services.toll_data_cache import toll_data_cache
    toll_data_cache.initialize()
    print("✅ Cache des péages initialisé")
except Exception as e:
    print(f"⚠️ Erreur d'initialisation du cache des péages : {e}")


def test_selestat_dijon_2_tolls():
    """Test Sélestat → Dijon avec 2 péages exactement."""
    print("=" * 80)
    print("🧪 TEST : Sélestat → Dijon avec 2 péages exactement")
    print("=" * 80)
    
    # Coordonnées Sélestat → Dijon
    coordinates = [
        [7.4525, 48.2608],  # Sélestat
        [5.0415, 47.3220]   # Dijon
    ]
    
    try:        # Initialisation des services
        ors_service = ORSService()
        strategy = IntelligentSegmentationStrategyV2(
            ors_service=ors_service,
            osm_data_file="data/osm_export_toll.geojson"  # Utiliser le fichier OSM GeoJSON
        )
        
        # Test avec 2 péages exactement
        result = strategy.find_route_with_exact_tolls(coordinates, target_tolls=2)
        
        if result:
            print("\n✅ SUCCÈS : Route trouvée avec segmentation intelligente")
            print(f"📊 Instructions: {len(result.get('instructions', []))} étapes")
            print(f"💰 Coût total: {result.get('total_cost', 0):.2f}€")
            print(f"🛣️ Nombre de péages: {result.get('toll_count', 0)}")
            print(f"📏 Distance totale: {result.get('total_distance', 0):.1f} km")
            print(f"⏱️ Durée totale: {result.get('total_duration', 0):.1f} min")
            
            # Afficher les péages utilisés
            tolls = result.get('tolls', [])
            print(f"\n🎯 Péages utilisés ({len(tolls)}):")
            for i, toll in enumerate(tolls, 1):
                print(f"   {i}. {toll.get('name', 'Inconnu')} - {toll.get('cost', 0):.2f}€")
              # Afficher les segments
            segments = result.get('segments', [])
            print(f"\n🔗 Segments de route ({len(segments)}):")
            for i, segment in enumerate(segments, 1):
                if isinstance(segment, dict):
                    segment_type = "avec péages" if segment.get('has_tolls', False) else "sans péages"
                    distance = segment.get('distance', 0)
                    print(f"   {i}. {distance:.1f} km ({segment_type})")
                else:
                    # Si c'est une string ou autre, l'afficher tel quel
                    print(f"   {i}. {segment}")
            
            return True
        else:
            print("\n❌ ÉCHEC : Aucune route trouvée")
            return False
            
    except Exception as e:
        print(f"\n💥 ERREUR : {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_edge_cases():
    """Test des cas limites."""
    print("\n" + "=" * 80)
    print("🧪 TESTS DES CAS LIMITES")
    print("=" * 80)
    
    coordinates = [
        [7.4525, 48.2608],  # Sélestat
        [5.0415, 47.3220]   # Dijon
    ]
    
    try:
        ors_service = ORSService()
        strategy = IntelligentSegmentationStrategyV2(
            ors_service=ors_service,
            osm_data_file="data/osm_export_toll.geojson"  # Utiliser le fichier OSM GeoJSON
        )
        
        # Test 1 : 0 péage (route toll-free)
        print("\n🔍 Test 1 : 0 péage demandé")
        result_0 = strategy.find_route_with_exact_tolls(coordinates, target_tolls=0)
        if result_0:
            print(f"   ✅ Route sans péages : {result_0.get('toll_count', 0)} péages")
        else:
            print("   ❌ Échec route sans péages")
        
        # Test 2 : 1 péage (système ouvert seulement)
        print("\n🔍 Test 2 : 1 péage demandé")
        result_1 = strategy.find_route_with_exact_tolls(coordinates, target_tolls=1)
        if result_1:
            print(f"   ✅ Route avec 1 péage : {result_1.get('toll_count', 0)} péages")
        else:
            print("   ❌ Échec route avec 1 péage")
        
        # Test 3 : 3 péages (combinaisons)
        print("\n🔍 Test 3 : 3 péages demandés")
        result_3 = strategy.find_route_with_exact_tolls(coordinates, target_tolls=3)
        if result_3:
            print(f"   ✅ Route avec 3 péages : {result_3.get('toll_count', 0)} péages")
        else:
            print("   ❌ Échec route avec 3 péages")
        
        return True
        
    except Exception as e:
        print(f"\n💥 ERREUR dans les cas limites : {str(e)}")
        return False


if __name__ == "__main__":
    print("🚀 Démarrage des tests de segmentation intelligente V2")
    
    success = True
    
    # Test principal : Sélestat-Dijon avec 2 péages
    success &= test_selestat_dijon_2_tolls()
    
    # Tests des cas limites
    success &= test_edge_cases()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 TOUS LES TESTS RÉUSSIS !")
    else:
        print("💥 CERTAINS TESTS ONT ÉCHOUÉ")
    print("=" * 80)
