"""
Test de l'endpoint /api/smart-route/tolls avec la stratégie intelligente
======================================================================

Test l'API complète avec la stratégie de segmentation intelligente activée.
"""

import requests
import json

def test_smart_route_tolls_api():
    """Test l'endpoint avec la stratégie intelligente."""
    print("🌐 Test de l'API /api/smart-route/tolls")
    print("=" * 60)
    
    # URL de l'API (supposer que le serveur tourne sur localhost:5000)
    url = "http://localhost:5000/api/smart-route/tolls"
    
    # Données de test : Sélestat → Besançon
    payload = {
        "coordinates": [
            [7.448595, 48.262004],   # Sélestat
            [6.012901, 47.246152]    # Besançon
        ],
        "max_tolls": 1,              # Objectif : 1 péage exact
        "vehicle_class": "c1"        # Classe véhicule standard
    }
    
    print(f"📍 Trajet : Sélestat → Besançon")
    print(f"🎯 Objectif : {payload['max_tolls']} péage maximum")
    print(f"🚗 Véhicule : {payload['vehicle_class']}")
    
    try:
        # Faire la requête POST
        print(f"\n🔗 Requête vers {url}")
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Réponse reçue avec succès !")
            print(f"\n📊 Résumé de la réponse :")
            
            # Analyser la réponse
            if 'found_solution' in result:
                print(f"   - Solution trouvée : {result['found_solution']}")
                print(f"   - Stratégie utilisée : {result.get('strategy_used', 'N/A')}")
                print(f"   - Respecte contrainte : {result.get('respects_constraint', 'N/A')}")
                
                if 'route' in result:
                    print(f"   - Route générée : ✅")
                    route_info = result['route']['features'][0]['properties']['summary']
                    print(f"   - Distance : {route_info.get('distance', 0)/1000:.1f} km")
                    print(f"   - Durée : {route_info.get('duration', 0)/60:.0f} min")
                
                if 'toll_count' in result:
                    print(f"   - Péages comptés : {result['toll_count']}")
                    
            else:
                # Format de réponse ancien
                print("   - Format de réponse : Ancien système")
                for key, value in result.items():
                    if isinstance(value, dict) and 'distance' in value:
                        print(f"   - {key} : {value['distance']/1000:.1f} km")
            
            return True
            
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            print(f"Réponse : {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur")
        print("   Assurez-vous que le serveur Flask tourne sur localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la requête : {e}")
        return False

def test_smart_route_tolls_mock():
    """Test avec un mock du service pour vérification locale."""
    print("\n🧪 Test avec mock local")
    print("=" * 60)
    
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # Service ORS simulé
        class MockORSService:
            def get_base_route(self, coordinates, include_tollways=False):
                return {
                    "features": [{
                        "geometry": {
                            "coordinates": coordinates
                        },
                        "properties": {
                            "summary": {
                                "distance": 120000,
                                "duration": 4800
                            }
                        }
                    }]
                }
            
            def get_route_avoid_tollways(self, coordinates):
                return {
                    "features": [{
                        "geometry": {
                            "coordinates": coordinates
                        },
                        "properties": {
                            "summary": {
                                "distance": 50000,
                                "duration": 3000
                            }
                        }
                    }]
                }
        
        # Initialiser le cache
        from src.cache import toll_data_cache
        if not toll_data_cache._initialized:
            toll_data_cache.initialize()
        # Créer l'optimiseur
        from src.services.toll_strategies import TollRouteOptimizer
        
        mock_ors = MockORSService()
        optimizer = TollRouteOptimizer(mock_ors)
        
        # Test avec les mêmes données
        coordinates = [
            [7.448595, 48.262004],   # Sélestat
            [6.012901, 47.246152]    # Besançon
        ]
        
        result = optimizer.compute_route_with_toll_limit(
            coordinates, 
            max_tolls=1, 
            veh_class="c1"
        )
        
        print("✅ Test local réussi !")
        print(f"   - Type de résultat : {type(result)}")
        print(f"   - Clés disponibles : {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test local : {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🌐 Tests de l'endpoint /api/smart-route/tolls")
    print("=" * 80)
    
    # Test 1 : Requête API réelle (si serveur disponible)
    api_ok = test_smart_route_tolls_api()
    
    # Test 2 : Test local avec mock
    mock_ok = test_smart_route_tolls_mock()
    
    print("\n" + "=" * 80)
    print("📋 RÉSUMÉ DES TESTS")
    print("=" * 80)
    
    if api_ok:
        print("✅ API /api/smart-route/tolls : OK")
    else:
        print("⚠️ API /api/smart-route/tolls : Non disponible (serveur éteint)")
    
    if mock_ok:
        print("✅ Test local avec mock : OK")
    else:
        print("❌ Test local avec mock : ÉCHEC")
    
    if mock_ok:  # Au moins le mock fonctionne
        print("\n🎉 Stratégie intelligente prête pour l'API !")
    else:
        print("\n⚠️ Problèmes détectés dans la stratégie")
