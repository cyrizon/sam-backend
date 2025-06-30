"""
Test pour diagnostiquer pourquoi la ré-analyse ne détecte qu'un seul péage
quand 2 péages ont été sélectionnés.
"""

import pytest
from src.services.toll.route_optimization.assembly.route_assembler import RouteAssembler
from src.services.toll.route_optimization.toll_analysis.toll_identifier import TollIdentifier


def test_reanalysis_missing_tolls():
    """
    Diagnostique pourquoi la ré-analyse dans RouteAssembler 
    ne détecte qu'un seul péage alors que 2 étaient prévus.
    """
    
    print("=" * 80)
    print("DIAGNOSTIC: PROBLÈME DE RÉ-ANALYSE DES PÉAGES")
    print("=" * 80)
    
    # Simuler une route finale qui devrait contenir 2 péages
    # Coordonnées d'exemple entre Strasbourg et Lyon (où il y a plusieurs péages)
    route_coordinates = [
        [7.448405, 48.261682],  # Strasbourg (départ)
        [7.4, 48.2],
        [7.3, 48.1],
        [7.2, 48.0],
        [7.1, 47.9],
        [7.0, 47.8],
        [6.9, 47.7],            # Près de Fontaine Larivière
        [6.8, 47.6],
        [6.7, 47.5],
        [6.6, 47.4],            # Près de Saint-Maurice
        [6.5, 47.3],
        [6.0, 47.0],
        [5.5, 46.5],
        [5.0, 46.0],
        [4.8, 45.8],            # Près de Villefranche-Limas
        [4.840976, 45.752127]   # Lyon (arrivée)
    ]
    
    # Péages théoriquement sélectionnés (d'après les logs précédents)
    selected_tolls = [
        {
            'osm_id': 'node/13835106',
            'name': 'Péage de Saint-Maurice',
            'toll_type': 'fermé',
            'coordinates': [6.6712671, 47.4255066],
            'operator': 'APRR'
        },
        {
            'osm_id': 'node/2408730611', 
            'name': 'Péage de Villefranche-Limas',
            'toll_type': 'fermé',
            'coordinates': [4.7319396, 45.9734404],
            'operator': 'APRR'
        }
    ]
    
    print(f"Route simulée: {len(route_coordinates)} points")
    print(f"Péages sélectionnés: {len(selected_tolls)}")
    for i, toll in enumerate(selected_tolls):
        print(f"  {i+1}. {toll['name']} à {toll['coordinates']}")
    
    print("\n" + "-" * 60)
    print("TEST 1: RÉ-ANALYSE DIRECTE AVEC TOLLIDENTIFIER")
    print("-" * 60)
    
    # Test direct avec TollIdentifier
    try:
        toll_identifier = TollIdentifier()
        reanalysis_result = toll_identifier.identify_tolls_on_route(route_coordinates, None)
        
        print(f"Succès identification: {reanalysis_result.get('identification_success')}")
        if reanalysis_result.get('identification_success'):
            actual_tolls = reanalysis_result.get('tolls_on_route', [])
            print(f"Péages détectés par ré-analyse: {len(actual_tolls)}")
            
            for i, toll_data in enumerate(actual_tolls):
                toll = toll_data.get('toll')
                if toll:
                    print(f"  {i+1}. {toll.name} à {toll.coordinates}")
                else:
                    print(f"  {i+1}. {toll_data}")
            
            # Comparer avec les péages sélectionnés
            detected_names = [toll_data.get('toll', {}).name if toll_data.get('toll') else 'Inconnu' 
                            for toll_data in actual_tolls]
            selected_names = [toll['name'] for toll in selected_tolls]
            
            print(f"\nComparaison:")
            print(f"Sélectionnés: {selected_names}")
            print(f"Détectés: {detected_names}")
            
            # Vérifier les correspondances
            matches = 0
            for selected in selected_names:
                if any(selected in detected for detected in detected_names):
                    matches += 1
            
            print(f"Correspondances: {matches}/{len(selected_names)}")
            
            if matches < len(selected_names):
                print("⚠️ PROBLÈME: Pas tous les péages sélectionnés détectés lors de la ré-analyse")
        else:
            print("❌ Échec de la ré-analyse")
            
    except Exception as e:
        print(f"❌ Erreur ré-analyse: {e}")
    
    print("\n" + "-" * 60)
    print("TEST 2: CALCUL DES COÛTS AVEC PÉAGES SÉLECTIONNÉS")
    print("-" * 60)
    
    # Test du calcul de coûts avec les péages sélectionnés (fallback)
    mock_route = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": route_coordinates
            },
            "properties": {
                "summary": {
                    "distance": 400000,  # 400km
                    "duration": 14400    # 4h
                }
            }
        }]
    }
    
    try:
        toll_cost, toll_count, toll_details = RouteAssembler._calculate_toll_costs_from_selected(
            mock_route, selected_tolls
        )
        
        print(f"Calcul avec péages sélectionnés:")
        print(f"  Coût total: {toll_cost}€")
        print(f"  Nombre de péages: {toll_count}")
        print(f"  Détails: {len(toll_details)} binômes")
        
        for detail in toll_details:
            print(f"    {detail.get('from_name')} → {detail.get('to_name')}: {detail.get('cost', 0)}€")
            
    except Exception as e:
        print(f"❌ Erreur calcul coûts: {e}")
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    
    # Retourner les résultats pour analyse
    return {
        'route_coordinates': route_coordinates,
        'selected_tolls': selected_tolls,
        'reanalysis_result': reanalysis_result if 'reanalysis_result' in locals() else None
    }


if __name__ == "__main__":
    test_reanalysis_missing_tolls()
