"""
Test de l'API d'optimisation avec logs détaillés
"""

import requests
import json

def test_optimization_api():
    """Test l'API smart-route avec 2 péages pour voir l'optimisation"""
    
    url = "http://127.0.0.1:5000/api/smart-route/tolls"
    
    # Route de Sélestat à Clermont-Ferrand
    payload = {
        "coordinates": [
            [7.448595, 48.262004],  # Sélestat
            [3.114432, 45.784832]   # Clermont-Ferrand
        ],
        "max_tolls": 2
    }
    
    print("🧪 Test API d'optimisation")
    print(f"   Route: Sélestat → Clermont-Ferrand")
    print(f"   Target: {payload['max_tolls']} péages")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        
        print(f"\n📡 Réponse API:")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Analyser la réponse - logique de succès améliorée
            api_success = data.get('success', False)
            found_solution = data.get('found_solution', '')
            respects_constraint = data.get('respects_constraint', False)
            
            # Détecter le vrai succès basé sur found_solution
            real_success = (api_success or 
                          found_solution in ['optimization_success', 'base_route_sufficient'] or
                          respects_constraint)
            
            print(f"   ✅ Succès API: {api_success}")
            print(f"   🎯 Vraie réussite: {real_success} (solution: {found_solution})")
            
            # Afficher toutes les clés disponibles pour debug
            print(f"   🔍 Clés de réponse: {list(data.keys())}")
            
            if not real_success:
                print(f"   ❌ Erreur API: {data.get('error', 'Erreur inconnue')}")
                print(f"   📝 Message: {data.get('message', 'Pas de message')}")
                
                # Essayer de voir les autres infos utiles même en cas d'erreur
                print(f"   🔍 Données disponibles malgré l'erreur:")
                print(f"      found_solution: {data.get('found_solution', False)}")
                print(f"      strategy_used: {data.get('strategy_used', 'N/A')}")
                print(f"      toll_count: {data.get('toll_count', 0)}")
                print(f"      respects_constraint: {data.get('respects_constraint', False)}")
                print(f"      target_tolls: {data.get('target_tolls', 'N/A')}")
                print(f"      cost: {data.get('cost', 0):.2f}€")
                
                # Corriger les unités de distance et durée
                distance_raw = data.get('distance', 0)
                duration_raw = data.get('duration', 0)
                
                # Si la distance semble en mètres (> 1000), convertir en km
                if distance_raw > 1000:
                    distance_km = distance_raw / 1000
                    print(f"      distance: {distance_km:.1f}km (converti de {distance_raw:.1f}m)")
                else:
                    print(f"      distance: {distance_raw:.1f}km")
                
                # Si la durée semble en secondes (> 60), convertir en minutes
                if duration_raw > 60:
                    duration_min = duration_raw / 60
                    print(f"      duration: {duration_min:.1f}min (converti de {duration_raw:.1f}s)")
                else:
                    print(f"      duration: {duration_raw:.1f}min")
                
                # Regarder les péages trouvés
                tolls = data.get('tolls', [])
                if isinstance(tolls, list) and tolls:
                    print(f"      Péages trouvés ({len(tolls)}):")
                    for i, toll in enumerate(tolls[:3]):
                        if isinstance(toll, dict):
                            toll_name = toll.get('name', toll.get('nom', 'Inconnu'))
                            toll_type = toll.get('type', 'N/A')
                            print(f"         {i+1}. {toll_name} ({toll_type})")
                        else:
                            print(f"         {i+1}. {toll}")
                elif tolls:
                    print(f"      Péages: {tolls}")
                
                # Regarder les segments - adaptation robuste
                segments = data.get('segments', [])
                if isinstance(segments, list) and segments:
                    print(f"      Segments créés: {len(segments)}")
                    for i, seg in enumerate(segments[:2]):
                        if isinstance(seg, dict):
                            print(f"         Segment {i+1}: {seg.get('type', 'N/A')}")
                        else:
                            print(f"         Segment {i+1}: {seg}")
                elif segments:
                    print(f"      Segments: {type(segments).__name__} - {segments}")
                else:
                    print(f"      Segments: Aucun")
                
                # Afficher toll_info si disponible
                toll_info = data.get('toll_info', {})
                if isinstance(toll_info, dict) and toll_info:
                    print(f"      Toll info:")
                    for key, value in toll_info.items():
                        print(f"         {key}: {value}")
                elif toll_info:
                    print(f"      Toll info: {toll_info}")
            
            # Afficher les informations de route
            if real_success:
                print(f"\n   🎉 OPTIMISATION RÉUSSIE!")
                print(f"      Stratégie: {data.get('strategy_used', 'N/A')}")
                print(f"      Péages trouvés: {data.get('toll_count', 0)}")
                print(f"      Contrainte respectée: {data.get('respects_constraint', False)}")
                print(f"      Coût total: {data.get('cost', 0):.2f}€")
                
                distance_raw = data.get('distance', 0)
                duration_raw = data.get('duration', 0)
                
                if distance_raw > 1000:
                    print(f"      Distance: {distance_raw/1000:.1f}km")
                else:
                    print(f"      Distance: {distance_raw:.1f}km")
                    
                if duration_raw > 60:
                    print(f"      Durée: {duration_raw/60:.1f}min")
                else:
                    print(f"      Durée: {duration_raw:.1f}min")
                
                # Afficher les péages sélectionnés depuis toll_info
                toll_info = data.get('toll_info', {})
                if toll_info and 'selected_tolls' in toll_info:
                    selected = toll_info['selected_tolls']
                    print(f"      Péages sélectionnés: {selected}")
                    if 'toll_systems' in toll_info:
                        print(f"      Systèmes: {toll_info['toll_systems']}")
            else:
                print(f"\n   ❌ OPTIMISATION ÉCHOUÉE")
                print(f"      Raison: {data.get('found_solution', 'Erreur inconnue')}")
            
            # Afficher les informations de route si succès API classique
            if data.get('success', False):
                print(f"   ✅ Optimisation réussie!")
                print(f"      Stratégie: {data.get('strategy_used', 'N/A')}")
                print(f"      Péages: {data.get('toll_count', 0)}")
                print(f"      Contrainte respectée: {data.get('respects_constraint', False)}")
                print(f"      Coût: {data.get('cost', 0):.2f}€")
                print(f"      Distance: {data.get('distance', 0):.1f}km")
                print(f"      Durée: {data.get('duration', 0):.1f}min")
            
            # Afficher la route si disponible
            route = data.get('route')
            if route and isinstance(route, dict):
                print(f"   📊 Route:")
                if 'features' in route:
                    print(f"      Features: {len(route['features'])}")
                if 'properties' in route:
                    props = route['properties']
                    print(f"      Distance totale: {props.get('summary', {}).get('distance', 0)/1000:.1f}km")
                    print(f"      Durée totale: {props.get('summary', {}).get('duration', 0)/60:.1f}min")
            
            # Afficher les instructions si disponibles
            instructions = data.get('instructions', [])
            if isinstance(instructions, list) and instructions:
                print(f"   📝 Instructions: {len(instructions)} étapes")
                for i, instruction in enumerate(instructions[:3]):
                    if isinstance(instruction, dict):
                        text = instruction.get('instruction', instruction.get('text', 'N/A'))
                        print(f"      {i+1}. {text}")
            elif instructions:
                print(f"   📝 Instructions: {instructions}")
            
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
                if isinstance(selected_tolls, list) and selected_tolls:
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
                elif selected_tolls:
                    print(f"      Péages sélectionnés: {selected_tolls}")
        
        else:
            print(f"   ❌ Erreur: {response.status_code}")
            print(f"   Message: {response.text}")
    
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erreur requête: {e}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    test_optimization_api()
