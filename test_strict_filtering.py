"""
Test de validation de la distance ultra-stricte (1m) pour éviter les péages côté opposé.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.toll.new_segmentation.polyline_intersection import filter_tolls_on_route_strict


def test_strict_distance_filtering():
    """Test que la distance de 1m filtre bien les péages côté opposé."""
    
    # Route simulée (ligne droite est-ouest)
    route_coords = [
        [7.0, 47.5],  # Point A
        [6.5, 47.5],  # Point B
        [6.0, 47.5],  # Point C
    ]
    
    # Péages simulés
    tolls_data = [
        {
            'id': 'toll_on_route',
            'name': 'Péage sur la route',
            'coordinates': [6.5, 47.5],  # Exactement sur la route
            'highway': 'toll_gantry'
        },
        {
            'id': 'toll_very_close',
            'name': 'Péage très proche',
            'coordinates': [6.5, 47.50001],  # 0.1m de la route (≈11cm)
            'highway': 'toll_gantry'
        },
        {
            'id': 'toll_opposite_side',
            'name': 'Péage côté opposé',
            'coordinates': [6.5, 47.5005],  # 50m de la route (côté opposé)
            'highway': 'toll_gantry'
        },
        {
            'id': 'toll_far_away',
            'name': 'Péage loin',
            'coordinates': [6.5, 47.501],  # 100m de la route
            'highway': 'toll_gantry'
        }
    ]
    
    print(f"\n🧪 Test filtrage ultra-strict (1m) :")
    print(f"   Route : {route_coords}")
    print(f"   Péages à tester : {len(tolls_data)}")
    
    # Test avec 100m (ancien comportement)
    tolls_100m = filter_tolls_on_route_strict(
        tolls_data, 
        route_coords, 
        max_distance_m=100,
        coordinate_attr='coordinates'
    )
    
    # Test avec 1m (nouveau comportement)
    tolls_1m = filter_tolls_on_route_strict(
        tolls_data, 
        route_coords, 
        max_distance_m=1,
        coordinate_attr='coordinates'    )
    
    print(f"\n📊 Résultats :")
    print(f"   Avec 100m : {len(tolls_100m)} péages détectés")
    for toll_data in tolls_100m:
        toll, distance, projection = toll_data
        print(f"      ✅ {toll['name']} : {distance:.1f}m")
    
    print(f"   Avec 1m : {len(tolls_1m)} péages détectés")
    for toll_data in tolls_1m:
        toll, distance, projection = toll_data
        print(f"      ✅ {toll['name']} : {distance:.1f}m")
    
    # Validation
    assert len(tolls_100m) >= len(tolls_1m), "Le filtrage 1m devrait être plus strict"
    
    # Vérifier que seuls les péages vraiment proches sont gardés avec 1m
    for toll_data in tolls_1m:
        toll, distance, projection = toll_data
        assert distance <= 1.0, f"Péage {toll['name']} trop loin : {distance}m"
        print(f"      ✅ {toll['name']} validé (≤ 1m)")
    
    print(f"\n✅ Test réussi ! Le filtrage 1m est plus précis.")
    return tolls_1m


if __name__ == "__main__":
    tolls = test_strict_distance_filtering()
