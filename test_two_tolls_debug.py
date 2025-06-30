"""
Test pour diagnostiquer le problème de sélection de 2 péages
Reproduit le cas où 2 péages sont demandés mais seulement 1 est retourné
"""

import pytest
from src.services.toll.route_optimization.toll_analysis.toll_selector import TollSelector


def test_two_tolls_selection_debug():
    """Diagnostique pourquoi la sélection de 2 péages retourne parfois 1 seul péage."""
    
    # Simuler une situation typique: 5 péages détectés, 2 demandés
    tolls_on_route = [
        {
            'osm_id': '1',
            'name': 'Péage A14 Orgeval',
            'toll_type': 'ouvert',
            'coordinates': [2.0, 49.0],
            'operator': 'VINCI'
        },
        {
            'osm_id': '2', 
            'name': 'Barrière Saint-Arnoult',
            'toll_type': 'fermé',
            'coordinates': [2.1, 49.1],
            'operator': 'VINCI'
        },
        {
            'osm_id': '3',
            'name': 'Barrière Dourdan',
            'toll_type': 'fermé', 
            'coordinates': [2.2, 49.2],
            'operator': 'VINCI'
        },
        {
            'osm_id': '4',
            'name': 'Barrière Étampes',
            'toll_type': 'fermé',
            'coordinates': [2.3, 49.3],
            'operator': 'VINCI'
        },
        {
            'osm_id': '5',
            'name': 'Barrière Nemours',
            'toll_type': 'fermé',
            'coordinates': [2.4, 49.4],
            'operator': 'VINCI'
        }
    ]
    
    # Mock identification_result 
    identification_result = {
        'route_coordinates': [[2.0, 49.0], [2.5, 49.5]],
        'tolls_on_route': tolls_on_route,
        'total_tolls_on_route': 5
    }
    
    # Créer le sélecteur
    selector = TollSelector()
    
    print("=" * 60)
    print("TEST: SÉLECTION DE 2 PÉAGES SUR 5 DISPONIBLES")
    print("=" * 60)
    print(f"Péages disponibles: {len(tolls_on_route)}")
    for i, toll in enumerate(tolls_on_route):
        print(f"  {i+1}. {toll['name']} ({toll['toll_type']})")
    print(f"Objectif: 2 péages")
    print("-" * 60)
    
    # Test de sélection
    result = selector.select_tolls_by_count(tolls_on_route, 2, identification_result)
    
    print("\nRÉSULTAT:")
    print(f"selection_valid: {result.get('selection_valid')}")
    print(f"selected_tolls: {len(result.get('selected_tolls', []))}")
    print(f"selection_count: {result.get('selection_count')}")
    print(f"optimized_elements: {len(result.get('optimized_elements', []))}")
    
    # Analyser les péages sélectionnés
    selected_tolls = result.get('selected_tolls', [])
    for i, toll in enumerate(selected_tolls):
        print(f"  Sélectionné {i+1}: {toll.get('name')} ({toll.get('toll_type')})")
    
    # Analyser les éléments optimisés
    optimized_elements = result.get('optimized_elements', [])
    print(f"\nÉléments optimisés: {len(optimized_elements)}")
    for i, element in enumerate(optimized_elements):
        if hasattr(element, 'osm_id'):
            print(f"  Optimisé {i+1}: TollBoothStation {element.osm_id}")
        else:
            print(f"  Optimisé {i+1}: {type(element).__name__}")
    
    # Vérifications
    assert result['selection_valid'], "La sélection devrait être valide"
    
    # PROBLÈME POTENTIEL: Vérifier si l'optimisation réduit le nombre d'éléments
    expected_count = 2
    actual_selected = len(selected_tolls)
    actual_optimized = len(optimized_elements)
    
    print(f"\nANALYSE:")
    print(f"Péages attendus: {expected_count}")
    print(f"Péages sélectionnés: {actual_selected}")
    print(f"Éléments optimisés: {actual_optimized}")
    
    if actual_selected != expected_count:
        print(f"⚠️ PROBLÈME 1: {actual_selected} péages sélectionnés au lieu de {expected_count}")
    
    if actual_optimized != expected_count:
        print(f"⚠️ PROBLÈME 2: {actual_optimized} éléments optimisés au lieu de {expected_count}")
    
    # Test détaillé de la logique de suppression
    print("\n" + "=" * 60)
    print("ANALYSE DÉTAILLÉE DE LA LOGIQUE DE SUPPRESSION")
    print("=" * 60)
    
    step1_result = selector._remove_tolls_to_match_count(tolls_on_route, 2)
    print(f"Étape 1 - selection_valid: {step1_result.get('selection_valid')}")
    print(f"Étape 1 - selected_tolls: {len(step1_result.get('selected_tolls', []))}")
    print(f"Étape 1 - removed_tolls: {len(step1_result.get('removed_tolls', []))}")
    
    for toll in step1_result.get('selected_tolls', []):
        print(f"  Gardé: {toll.get('name')} ({toll.get('toll_type')})")
    
    for toll in step1_result.get('removed_tolls', []):
        print(f"  Supprimé: {toll.get('name')} ({toll.get('toll_type')})")
        
    return result


if __name__ == "__main__":
    test_two_tolls_selection_debug()
