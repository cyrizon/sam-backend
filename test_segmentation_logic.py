"""
Test spécifique pour valider la logique de segmentation intelligente.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.toll.new_segmentation.toll_segment_builder import TollSegmentBuilder
from src.cache.models.matched_toll import MatchedToll


def test_segmentation_logic():
    """Test de la logique de segmentation avec péages à éviter."""
    
    # Coordonnées test (Sélestat → Dijon)
    start_coords = [7.452806, 48.259206]  # Sélestat
    end_coords = [5.041480, 47.322047]    # Dijon
    
    # Route simulée
    route_coords = [
        [7.452806, 48.259206],  # Départ
        [6.8, 47.8],            # Point intermédiaire 1
        [6.5, 47.6],            # Point intermédiaire 2
        [6.0, 47.4],            # Point intermédiaire 3
        [5.5, 47.3],            # Point intermédiaire 4
        [5.041480, 47.322047]   # Arrivée
    ]
      # Péages simulés
    all_tolls = [
        MatchedToll(
            osm_id="toll_1",
            osm_name="Péage A",
            osm_coordinates=[6.7, 47.7],
            csv_id=None,
            csv_name="Péage A",
            csv_role='O',
            csv_coordinates=None,
            distance_m=0.0,
            confidence=1.0
        ),
        MatchedToll(
            osm_id="toll_2", 
            osm_name="Péage B",
            osm_coordinates=[6.3, 47.5],
            csv_id=None,
            csv_name="Péage B",
            csv_role='O',
            csv_coordinates=None,
            distance_m=0.0,
            confidence=1.0
        ),
        MatchedToll(
            osm_id="toll_3",
            osm_name="Péage C", 
            osm_coordinates=[5.8, 47.35],
            csv_id=None,
            csv_name="Péage C",
            csv_role='O',
            csv_coordinates=None,
            distance_m=0.0,
            confidence=1.0
        )
    ]
    
    # Péages sélectionnés : éviter A et B, prendre C
    selected_tolls = [all_tolls[2]]  # Seulement le péage C
    
    print(f"\n🧪 Test de segmentation :")
    print(f"   Départ : {start_coords}")
    print(f"   Arrivée : {end_coords}")
    print(f"   Tous les péages : {[t.effective_name for t in all_tolls]}")
    print(f"   Péages sélectionnés : {[t.effective_name for t in selected_tolls]}")
    print(f"   Péages à éviter : {[t.effective_name for t in all_tolls if t not in selected_tolls]}")
      # Créer le service (avec un mock ORS simple)
    class MockORS:
        pass
    
    service = TollSegmentBuilder(MockORS())
    
    # Construire les segments
    segments = service.build_intelligent_segments(
        start_coords=start_coords,
        end_coords=end_coords,
        all_tolls_on_route=all_tolls,
        selected_tolls=selected_tolls,
        route_coords=route_coords
    )
    
    print(f"\n📊 Résultats :")
    print(f"   Nombre de segments : {len(segments)}")
    
    for i, segment in enumerate(segments, 1):
        print(f"   Segment {i} ({segment['type']}) : {segment['description']}")
        print(f"      Départ : {segment['start']}")
        print(f"      Arrivée : {segment['end']}")
    
    # Validation
    assert len(segments) > 0, "Aucun segment généré"
    
    # Le premier segment devrait éviter les péages avant
    first_segment = segments[0]
    assert first_segment['type'] == 'avoid_tolls', f"Premier segment devrait éviter les péages, reçu : {first_segment['type']}"
    
    # Vérifier que le premier segment ne va pas directement au péage C
    toll_c_coords = all_tolls[2].osm_coordinates
    first_end = first_segment['end']
    
    # Le premier segment ne devrait PAS finir exactement au péage C
    is_direct_to_toll = (first_end[0] == toll_c_coords[0] and first_end[1] == toll_c_coords[1])
    assert not is_direct_to_toll, f"Le premier segment ne devrait pas aller directement au péage C. Fin : {first_end}, Péage C : {toll_c_coords}"
    
    print(f"\n✅ Test réussi ! Le premier segment évite bien les péages et trouve une entrée stratégique.")
    return segments


if __name__ == "__main__":
    segments = test_segmentation_logic()
