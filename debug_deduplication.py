#!/usr/bin/env python3
"""
Script de débogage pour tester la déduplication des péages.
"""

import sys
import os
import json
from typing import List, Dict

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from cache.v2.managers.v2_cache_manager_with_linking import V2CacheManagerWithLinking
from services.toll.route_optimization.toll_analysis.toll_identifier import TollIdentifier


def test_specific_duplicates():
    """Test avec des coordonnées spécifiques connues pour avoir des doublons."""
    print("🔍 Test de déduplication avec des coordonnées spécifiques...")
    
    # Initialiser le cache V2
    print("📥 Chargement du cache V2...")
    cache_manager = V2CacheManagerWithLinking('osm_cache_v2_test')
    cache_manager.load_all_including_motorway_linking()
    
    # Créer l'identifier
    identifier = TollIdentifier()
    
    # Test avec une route qui passe par l'A6 avec des péages connus
    # Route A6 Paris -> Lyon avec plusieurs péages
    test_coordinates = [
        [2.3522, 48.8566],   # Paris
        [2.6945, 47.4737],   # Fontainebleau/Nemours
        [3.0639, 47.0831],   # Sens
        [3.5590, 47.8210],   # Auxerre Nord
        [3.5700, 47.8100],   # Auxerre Sud
        [4.0556, 46.6667],   # Chalon-sur-Saône
        [4.8357, 45.7640],   # Lyon
    ]
    
    print(f"🛣️  Test route avec {len(test_coordinates)} points...")
    
    # Identifier les péages
    result = identifier.identify_tolls_on_route(test_coordinates)
    
    if result['identification_success']:
        print(f"\n📊 Résultats d'identification :")
        print(f"   Péages sur route : {result['total_tolls_on_route']}")
        print(f"   Péages à proximité : {len(result['nearby_tolls'])}")
        
        if 'duplicates_removed' in result:
            print(f"   Doublons supprimés : {result['duplicates_removed']}")
        
        # Analyser les péages trouvés
        if result['tolls_on_route']:
            print(f"\n🎯 Péages identifiés sur la route :")
            for i, toll_data in enumerate(result['tolls_on_route']):
                toll = toll_data['toll']
                coords = toll_data['coordinates']
                distance = toll_data['min_distance_m']
                
                print(f"   {i+1}. {getattr(toll, 'nom', 'Sans nom')} "
                      f"({getattr(toll, 'operator', 'Inconnu')}) "
                      f"- OSM ID: {getattr(toll, 'osm_id', 'N/A')} "
                      f"- Distance: {distance:.1f}m "
                      f"- Coords: [{coords[0]:.6f}, {coords[1]:.6f}]")
            
            # Chercher manuellement les potentiels doublons
            print(f"\n🔍 Analyse manuelle des doublons potentiels :")
            for i, toll_data_1 in enumerate(result['tolls_on_route']):
                for j, toll_data_2 in enumerate(result['tolls_on_route']):
                    if i >= j:
                        continue
                    
                    # Calculer distance entre les deux
                    coords1 = toll_data_1['coordinates']
                    coords2 = toll_data_2['coordinates']
                    
                    # Distance simple (approximation)
                    import math
                    lat1, lon1 = coords1[1], coords1[0]
                    lat2, lon2 = coords2[1], coords2[0]
                    
                    # Formule haversine
                    R = 6371000
                    lat1_rad = math.radians(lat1)
                    lat2_rad = math.radians(lat2)
                    delta_lat = math.radians(lat2 - lat1)
                    delta_lon = math.radians(lon2 - lon1)
                    
                    a = (math.sin(delta_lat / 2) ** 2 + 
                         math.cos(lat1_rad) * math.cos(lat2_rad) * 
                         math.sin(delta_lon / 2) ** 2)
                    
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                    distance_m = R * c
                    
                    toll1 = toll_data_1['toll']
                    toll2 = toll_data_2['toll']
                    
                    name1 = getattr(toll1, 'nom', 'Sans nom')
                    name2 = getattr(toll2, 'nom', 'Sans nom')
                    op1 = getattr(toll1, 'operator', 'Inconnu')
                    op2 = getattr(toll2, 'operator', 'Inconnu')
                    
                    if distance_m < 50:  # Dans les 50m
                        print(f"   ⚠️  Doublons potentiels à {distance_m:.1f}m :")
                        print(f"       1. {name1} ({op1}) - OSM ID: {getattr(toll1, 'osm_id', 'N/A')}")
                        print(f"       2. {name2} ({op2}) - OSM ID: {getattr(toll2, 'osm_id', 'N/A')}")
                        
                        # Tester la fonction de déduplication manuellement
                        from services.toll.route_optimization.toll_analysis.core_identifier import CoreTollIdentifier
                        core = CoreTollIdentifier()
                        
                        are_dupes = core._are_tolls_duplicates(toll_data_1, toll_data_2)
                        print(f"       Détection doublon : {'OUI' if are_dupes else 'NON'}")
                        
                        if distance_m < 1.0:
                            print(f"       🔴 DOUBLON PROBABLE (<1m) mais non détecté par l'algorithme!")
        
        else:
            print(f"\n❌ Aucun péage trouvé sur la route")
    else:
        print(f"\n❌ Échec d'identification")
    
    return result


def test_with_known_route():
    """Test avec une route API réelle."""
    print("\n" + "="*60)
    print("🔍 Test avec route API réelle...")
    
    # Utiliser des coordonnées d'une vraie route avec des péages
    # Route A6 Paris -> Lyon (autoroute à péage principale)
    real_route = [
        [2.3522, 48.8566],   # Paris
        [2.6945, 47.4737],   # Fontainebleau
        [3.0639, 47.0831],   # Sens  
        [3.5590, 47.8210],   # Auxerre
        [4.0556, 46.6667],   # Chalon-sur-Saône
        [4.8357, 45.7640],   # Lyon
    ]
    
    cache_manager = V2CacheManagerWithLinking('osm_cache_v2_test')
    cache_manager.load_all_including_motorway_linking()
    identifier = TollIdentifier()
    
    result = identifier.identify_tolls_on_route(real_route)
    
    print(f"📊 Résultats avec route réelle :")
    print(f"   Péages trouvés : {result['total_tolls_on_route']}")
    if 'duplicates_removed' in result:
        print(f"   Doublons supprimés : {result['duplicates_removed']}")
    
    # Chercher spécifiquement "Auxerre" dans les résultats
    auxerre_tolls = []
    for toll_data in result.get('tolls_on_route', []):
        toll = toll_data['toll']
        name = getattr(toll, 'nom', '').lower()
        if 'auxerre' in name:
            auxerre_tolls.append(toll_data)
    
    if auxerre_tolls:
        print(f"\n🎯 Péages Auxerre trouvés : {len(auxerre_tolls)}")
        for i, toll_data in enumerate(auxerre_tolls):
            toll = toll_data['toll']
            print(f"   {i+1}. {getattr(toll, 'nom', 'Sans nom')} "
                  f"({getattr(toll, 'operator', 'Inconnu')}) "
                  f"- OSM ID: {getattr(toll, 'osm_id', 'N/A')}")
        
        if len(auxerre_tolls) > 1:
            print(f"   ⚠️  Plusieurs péages Auxerre détectés - vérification doublons...")
            for i in range(len(auxerre_tolls)):
                for j in range(i+1, len(auxerre_tolls)):
                    toll_data_1 = auxerre_tolls[i]
                    toll_data_2 = auxerre_tolls[j]
                    
                    coords1 = toll_data_1['coordinates']
                    coords2 = toll_data_2['coordinates']
                    
                    # Calculer distance
                    import math
                    lat1, lon1 = coords1[1], coords1[0]
                    lat2, lon2 = coords2[1], coords2[0]
                    R = 6371000
                    lat1_rad = math.radians(lat1)
                    lat2_rad = math.radians(lat2)
                    delta_lat = math.radians(lat2 - lat1)
                    delta_lon = math.radians(lon2 - lon1)
                    a = (math.sin(delta_lat / 2) ** 2 + 
                         math.cos(lat1_rad) * math.cos(lat2_rad) * 
                         math.sin(delta_lon / 2) ** 2)
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                    distance_m = R * c
                    
                    print(f"   Distance entre Auxerre {i+1} et {j+1} : {distance_m:.1f}m")
                    
                    if distance_m < 1.0:
                        print(f"   🔴 DOUBLON DÉTECTÉ (<1m) - L'algorithme devrait les supprimer!")
    else:
        print(f"\n❌ Aucun péage Auxerre trouvé")


def main():
    """Point d'entrée principal."""
    print("🚀 Démarrage du test de déduplication...")
    
    try:
        # Test 1: Coordonnées spécifiques
        result1 = test_specific_duplicates()
        
        # Test 2: Route réelle
        test_with_known_route()
        
        print(f"\n✅ Tests terminés")
        
    except Exception as e:
        print(f"❌ Erreur durant les tests : {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
