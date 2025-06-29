#!/usr/bin/env python3
"""
Test de déduplication en conditions réelles avec l'API.
"""

import requests
import json
import sys
import os

def test_api_deduplication():
    """Test la déduplication via l'API réelle."""
    print("🔍 Test de déduplication via API réelle...")
    
    # URL de l'API
    api_url = "http://localhost:5000/api/tolls"
    
    # Route test qui devrait avoir des doublons
    # Utilisons une route simple mais connue pour avoir des péages
    test_route = {
        "coordinates": [
            [2.3522, 48.8566],   # Paris
            [2.6500, 47.5000],   # Vers Fontainebleau
            [3.0500, 47.1000],   # Vers Sens
            [3.5590, 47.8210],   # Auxerre (zone connue avec doublons potentiels)
            [4.0000, 46.7000],   # Vers Chalon
            [4.8357, 45.7640]    # Lyon
        ]
    }
    
    print(f"🛣️  Test avec route de {len(test_route['coordinates'])} points")
    print(f"   De: Paris [{test_route['coordinates'][0]}]")
    print(f"   À: Lyon [{test_route['coordinates'][-1]}]")
    
    try:
        # Appel API
        print("\n📡 Appel API...")
        response = requests.post(api_url, json=test_route, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Réponse API reçue")
            print(f"📊 Statistiques:")
            print(f"   Péages trouvés: {len(result.get('tolls', []))}")
            
            # Analyser les résultats pour chercher des doublons
            tolls = result.get('tolls', [])
            
            if tolls:
                print(f"\n🎯 Péages identifiés:")
                for i, toll in enumerate(tolls):
                    print(f"   {i+1}. {toll.get('nom', 'Sans nom')} "
                          f"({toll.get('operator', 'Inconnu')}) "
                          f"- ID: {toll.get('id', 'N/A')} "
                          f"- Distance: {toll.get('distance_route', 'N/A')}m "
                          f"- Coords: [{toll.get('longitude', 'N/A')}, {toll.get('latitude', 'N/A')}]")
                
                # Détecter manuellement les doublons potentiels
                print(f"\n🔍 Analyse des doublons potentiels:")
                duplicates_found = 0
                
                for i in range(len(tolls)):
                    for j in range(i+1, len(tolls)):
                        toll1 = tolls[i]
                        toll2 = tolls[j]
                        
                        # Calculer distance entre les péages
                        lat1 = toll1.get('latitude')
                        lon1 = toll1.get('longitude')
                        lat2 = toll2.get('latitude')
                        lon2 = toll2.get('longitude')
                        
                        if lat1 and lon1 and lat2 and lon2:
                            import math
                            
                            # Formule haversine
                            R = 6371000  # Rayon de la Terre en mètres
                            lat1_rad = math.radians(lat1)
                            lat2_rad = math.radians(lat2)
                            delta_lat = math.radians(lat2 - lat1)
                            delta_lon = math.radians(lon2 - lon1)
                            
                            a = (math.sin(delta_lat / 2) ** 2 + 
                                 math.cos(lat1_rad) * math.cos(lat2_rad) * 
                                 math.sin(delta_lon / 2) ** 2)
                            
                            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                            distance_m = R * c
                            
                            # Vérifier les critères de doublon
                            name1 = toll1.get('nom', '').lower()
                            name2 = toll2.get('nom', '').lower()
                            op1 = toll1.get('operator', '')
                            op2 = toll2.get('operator', '')
                            autoroute1 = toll1.get('autoroute', '')
                            autoroute2 = toll2.get('autoroute', '')
                            
                            # Critères de doublon : distance < 1m ET similarité sémantique
                            is_close = distance_m < 1.0
                            same_name = name1 == name2 or (name1 and name2 and (name1 in name2 or name2 in name1))
                            same_operator = op1 == op2 or (not op1 or not op2)  # Si l'un est vide
                            same_autoroute = autoroute1 == autoroute2 or (not autoroute1 or not autoroute2)
                            
                            is_semantic_duplicate = same_name and same_operator and same_autoroute
                            
                            if distance_m < 50:  # Afficher tous les péages proches
                                print(f"   📏 Distance {distance_m:.1f}m entre:")
                                print(f"      {i+1}. {toll1.get('nom', 'Sans nom')} ({toll1.get('operator', 'Inconnu')}) - ID: {toll1.get('id', 'N/A')}")
                                print(f"      {j+1}. {toll2.get('nom', 'Sans nom')} ({toll2.get('operator', 'Inconnu')}) - ID: {toll2.get('id', 'N/A')}")
                                
                                if is_close and is_semantic_duplicate:
                                    print(f"      🔴 DOUBLON DÉTECTÉ ! (<1m + similarité sémantique)")
                                    duplicates_found += 1
                                elif is_close:
                                    print(f"      ⚠️  Très proche (<1m) mais différent sémantiquement")
                                elif is_semantic_duplicate:
                                    print(f"      ⚠️  Même sémantique mais distance > 1m")
                
                if duplicates_found > 0:
                    print(f"\n🔴 PROBLÈME: {duplicates_found} doublons détectés dans la réponse API!")
                    print(f"   La déduplication ne fonctionne pas correctement.")
                else:
                    print(f"\n✅ Aucun doublon détecté - déduplication OK")
            
            else:
                print(f"\n❌ Aucun péage trouvé")
                
        else:
            print(f"❌ Erreur API: {response.status_code}")
            print(f"   Réponse: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Impossible de se connecter à l'API sur http://localhost:5000")
        print(f"   Assurez-vous que le serveur Flask est démarré")
    except Exception as e:
        print(f"❌ Erreur: {e}")


def test_specific_route():
    """Test avec une route spécifique connue pour avoir des doublons."""
    print(f"\n" + "="*60)
    print("🔍 Test avec route spécifique (Auxerre)...")
    
    api_url = "http://localhost:5000/api/tolls"
    
    # Route plus précise autour d'Auxerre (zone connue pour doublons)
    auxerre_route = {
        "coordinates": [
            [3.5500, 47.8100],   # Avant Auxerre
            [3.5590, 47.8210],   # Auxerre Nord
            [3.5650, 47.8250],   # Après Auxerre Nord
            [3.5700, 47.8300]    # Plus loin
        ]
    }
    
    try:
        response = requests.post(api_url, json=auxerre_route, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            tolls = result.get('tolls', [])
            
            print(f"📊 Péages trouvés autour d'Auxerre: {len(tolls)}")
            
            # Chercher spécifiquement les péages Auxerre
            auxerre_tolls = [toll for toll in tolls if 'auxerre' in toll.get('nom', '').lower()]
            
            if len(auxerre_tolls) > 1:
                print(f"🎯 Péages Auxerre trouvés: {len(auxerre_tolls)}")
                for i, toll in enumerate(auxerre_tolls):
                    print(f"   {i+1}. {toll.get('nom')} - ID: {toll.get('id')} - Coords: [{toll.get('longitude')}, {toll.get('latitude')}]")
                
                print(f"⚠️  ATTENTION: Plusieurs péages Auxerre - vérification nécessaire")
            else:
                print(f"✅ Un seul péage Auxerre ou aucun doublon")
                
        else:
            print(f"❌ Erreur API: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")


def main():
    """Point d'entrée principal."""
    print("🚀 Test de déduplication en conditions réelles")
    print("="*60)
    
    # Test 1: Route complète
    test_api_deduplication()
    
    # Test 2: Route spécifique Auxerre
    test_specific_route()
    
    print(f"\n✅ Tests terminés")


if __name__ == "__main__":
    main()
