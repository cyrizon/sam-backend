"""
Test Toll Selector Simplifié
============================

Test de la nouvelle logique simplifiée : suppression dans l'ordre + optimisation du premier fermé.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))


def create_test_tolls_in_order():
    """Crée des péages de test dans l'ordre de la route."""
    return [
        {
            'osm_id': '1001',
            'name': 'Péage A10 Orléans',
            'toll_type': 'fermé',
            'coordinates': [1.9, 47.9],
            'order': 1
        },
        {
            'osm_id': '1002', 
            'name': 'Péage A71 Vierzon',
            'toll_type': 'ouvert',
            'coordinates': [2.1, 47.2],
            'order': 2
        },
        {
            'osm_id': '1003',
            'name': 'Péage A20 Châteauroux',
            'toll_type': 'fermé',
            'coordinates': [1.7, 46.8],
            'order': 3
        },
        {
            'osm_id': '1004',
            'name': 'Péage A71 Bourges',
            'toll_type': 'fermé',
            'coordinates': [2.4, 47.1],
            'order': 4
        },
        {
            'osm_id': '1005',
            'name': 'Péage A10 Tours',
            'toll_type': 'ouvert',
            'coordinates': [0.7, 47.4],
            'order': 5
        }
    ]


def test_removal_logic():
    """Test de la logique de suppression dans l'ordre."""
    print("🧪 Test logique de suppression dans l'ordre...")
    
    tolls = create_test_tolls_in_order()
    print(f"   📊 Péages initiaux : {len(tolls)}")
    for i, toll in enumerate(tolls):
        print(f"     {i+1}. {toll['name']} ({toll['toll_type']})")
    
    # Simuler la logique de suppression
    print(f"\n   🎯 Test : supprimer 2 péages (garder 3)")
    
    # Logique attendue : supprimer les 2 premiers fermés
    remaining_tolls = tolls.copy()
    removed_tolls = []
    to_remove_count = 2
    
    for _ in range(to_remove_count):
        # Chercher le premier fermé
        toll_to_remove = None
        for toll in remaining_tolls:
            if toll.get('toll_type') == 'fermé':
                toll_to_remove = toll
                break
        
        # Si pas de fermé, prendre le premier
        if toll_to_remove is None:
            toll_to_remove = remaining_tolls[0]
        
        remaining_tolls.remove(toll_to_remove)
        removed_tolls.append(toll_to_remove)
        print(f"   ❌ Supprimé: {toll_to_remove['name']} ({toll_to_remove['toll_type']})")
    
    print(f"\n   ✅ Péages conservés: {len(remaining_tolls)}")
    for toll in remaining_tolls:
        print(f"     - {toll['name']} ({toll['toll_type']})")
    
    # Vérifier la règle du péage fermé isolé
    closed_remaining = [t for t in remaining_tolls if t.get('toll_type') == 'fermé']
    print(f"\n   📊 Fermés restants: {len(closed_remaining)}")
    
    if len(closed_remaining) == 1:
        print("   ⚠️ RÈGLE: Péage fermé isolé détecté → route sans péage")
        return False, []
    
    # Identifier le premier fermé pour optimisation
    first_closed = None
    for toll in remaining_tolls:
        if toll.get('toll_type') == 'fermé':
            first_closed = toll
            break
    
    if first_closed:
        print(f"   🎯 Premier fermé à optimiser: {first_closed['name']}")
    
    return True, remaining_tolls


def test_with_toll_selector():
    """Test avec le vrai TollSelector."""
    print("\n🧪 Test avec TollSelector réel...")
    
    try:
        from src.services.toll.route_optimization.toll_analysis.toll_selector import TollSelector
        
        tolls = create_test_tolls_in_order()
        identification_result = {
            'route_info': {
                'start_point': [2.3522, 48.8566],  # Paris
                'end_point': [1.4442, 43.6043]      # Toulouse
            },
            'route_coordinates': [[2.3522, 48.8566], [1.4442, 43.6043]],
            'total_distance_km': 678.2
        }
        
        toll_selector = TollSelector()
        
        # Test avec 3 péages
        result = toll_selector.select_tolls_by_count(
            tolls_on_route=tolls,
            target_count=3,
            identification_result=identification_result
        )
        
        print(f"   ✅ Résultat:")
        print(f"     - Valid: {result.get('selection_valid')}")
        print(f"     - Count: {result.get('selection_count')}")
        print(f"     - Segments: {len(result.get('segments', []))}")
        print(f"     - Raison: {result.get('selection_reason', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return None


def main():
    """Test principal."""
    print("=" * 60)
    print("🚧 Test Logique Simplifiée de Sélection")
    print("=" * 60)
    
    # Test logique pure
    success, remaining = test_removal_logic()
    
    # Test avec TollSelector même si échec (pour voir le comportement)
    test_with_toll_selector()
    
    print("\n✅ Tests terminés!")


if __name__ == "__main__":
    main()
