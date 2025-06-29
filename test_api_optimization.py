"""
Test de l'API d'optimisation avec logs détaillés
"""

import requests
import json

def test_optimization_api():
    """Test l'API smart-route avec 2 péages pour voir l'optimisation"""
    
    url = "http://127.0.0.1:5000/api/smart-route/tolls"
    
    # Route de Sélestat à Dijon (comme dans les logs)
    payload = {
        "coordinates": [
            [7.448405, 48.261682],  # Sélestat
            [3.11506, 45.784359]    # Destination finale (proche Clermont-Ferrand)
        ],
        "target_tolls": 2,
        "optimization_mode": "count"
    }
    
    print("🧪 Test API d'optimisation")
    print(f"   Route: Sélestat → Clermont-Ferrand")
    print(f"   Target: {payload['target_tolls']} péages")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        
        print(f"\n📡 Réponse API:")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Analyser la réponse
            print(f"   ✅ Succès: {data.get('success', False)}")
            
            # Afficher toutes les clés disponibles pour debug
            print(f"   🔍 Clés de réponse: {list(data.keys())}")
            
            if not data.get('success', False):
                print(f"   ❌ Erreur API: {data.get('error', 'Erreur inconnue')}")
                print(f"   📝 Message: {data.get('message', 'Pas de message')}")
                
                # Essayer de voir les autres infos utiles même en cas d'erreur
                print(f"   🔍 Données disponibles malgré l'erreur:")
                print(f"      found_solution: {data.get('found_solution', False)}")
                print(f"      strategy_used: {data.get('strategy_used', 'N/A')}")
                print(f"      toll_count: {data.get('toll_count', 0)}")
                print(f"      respects_constraint: {data.get('respects_constraint', False)}")
                
                # Regarder les péages trouvés
                tolls = data.get('tolls', [])
                if tolls:
                    print(f"      Péages trouvés ({len(tolls)}):")
                    for i, toll in enumerate(tolls[:3]):
                        toll_name = toll.get('name', 'Inconnu')
                        toll_type = toll.get('type', 'N/A')
                        print(f"         {i+1}. {toll_name} ({toll_type})")
                
                # Regarder les segments
                segments = data.get('segments', [])
                if segments:
                    print(f"      Segments créés: {len(segments)}")
                    for i, seg in enumerate(segments[:2]):
                        print(f"         Segment {i+1}: {seg.get('type', 'N/A')}")
            
            if 'route_data' in data:
                route = data['route_data']
                print(f"   📊 Route assemblée:")
                print(f"      Distance: {route.get('total_distance_km', 0):.1f}km")
                print(f"      Durée: {route.get('total_time_min', 0):.1f}min")
                print(f"      Coût: {route.get('total_cost_eur', 0):.1f}€")
                print(f"      Péages: {route.get('total_tolls', 0)}")
            
            if 'debug_info' in data:
                debug = data['debug_info']
                print(f"   🔍 Debug:")
                print(f"      Péages identifiés: {debug.get('tolls_identified', 0)}")
                print(f"      Péages sélectionnés: {debug.get('tolls_selected', 0)}")
                print(f"      Optimisation appliquée: {debug.get('optimization_applied', False)}")
                print(f"      Éléments optimisés: {debug.get('elements_optimized', 0)}")
            
            # Regarder la sélection détaillée
            if 'selection_info' in data:
                selection = data['selection_info']
                print(f"   🎯 Sélection:")
                print(f"      Valide: {selection.get('selection_valid', False)}")
                print(f"      Raison: {selection.get('selection_reason', 'N/A')}")
                
                selected_tolls = selection.get('selected_tolls', [])
                print(f"      Péages sélectionnés ({len(selected_tolls)}):")
                for i, toll in enumerate(selected_tolls[:3]):  # Limiter l'affichage
                    if isinstance(toll, dict) and 'toll' in toll:
                        toll_obj = toll['toll']
                        toll_name = getattr(toll_obj, 'display_name', 'Inconnu')
                        toll_type = 'ouvert' if getattr(toll_obj, 'is_open_toll', False) else 'fermé'
                        print(f"         {i+1}. {toll_name} ({toll_type})")
                    elif hasattr(toll, 'display_name'):
                        toll_type = 'ouvert' if getattr(toll, 'is_open_toll', False) else 'fermé'
                        print(f"         {i+1}. {toll.display_name} ({toll_type})")
                    else:
                        print(f"         {i+1}. {toll}")
        
        else:
            print(f"   ❌ Erreur: {response.status_code}")
            print(f"   Message: {response.text}")
    
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erreur requête: {e}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    test_optimization_api()
