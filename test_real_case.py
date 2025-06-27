"""
Simulation exacte du cas Sélestat-Dijon avec les vrais noms de péages.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.toll.new_segmentation.toll_segment_builder import TollSegmentBuilder
from src.cache.models.matched_toll import MatchedToll


def test_selestat_dijon_real():
    """Test reproduisant exactement le cas Sélestat-Dijon."""
    
    # Coordonnées exactes de votre exemple
    start_coords = [7.448595, 48.262004]  # Sélestat
    end_coords = [5.037793, 47.317743]    # Dijon
    
    # Péages avec noms réels
    all_tolls = [
        MatchedToll(
            osm_id="toll_1",
            osm_name="Péage à éviter 1", 
            osm_coordinates=[7.0, 48.0],  # Quelque part avant
            csv_id=None,
            csv_name="Péage à éviter 1",
            csv_role='O',
            csv_coordinates=None,
            distance_m=0.0,
            confidence=1.0
        ),
        MatchedToll(
            osm_id="toll_saint_maurice",
            osm_name="Péage de Saint-Maurice",
            osm_coordinates=[6.6712671, 47.4255066],  # Coordonnées exactes de votre log
            csv_id=None,
            csv_name="Péage de Saint-Maurice", 
            csv_role='O',
            csv_coordinates=None,
            distance_m=0.0,
            confidence=1.0
        ),
        MatchedToll(
            osm_id="toll_dijon",
            osm_name="Péage de Dijon-Crimolois",
            osm_coordinates=[5.1380486, 47.2770761],  # Coordonnées exactes de votre log
            csv_id=None,
            csv_name="Péage de Dijon-Crimolois",
            csv_role='O',
            csv_coordinates=None,
            distance_m=0.0,
            confidence=1.0
        )
    ]
    
    # Scénario exacte : éviter le premier, prendre Saint-Maurice et Dijon
    selected_tolls = [all_tolls[1], all_tolls[2]]
    
    print(f"\n🎯 Simulation exacte Sélestat-Dijon :")
    print(f"   Départ : {start_coords}")
    print(f"   Arrivée : {end_coords}")
    print(f"   Péages sélectionnés : {[t.effective_name for t in selected_tolls]}")
    
    # Calcul des distances
    from src.services.toll.new_segmentation.segment_building.highway_entrance_analyzer import HighwayEntranceAnalyzer
    analyzer = HighwayEntranceAnalyzer(None)
    
    distance_peages = analyzer.calculate_distance_km(
        all_tolls[0].osm_coordinates, 
        all_tolls[1].osm_coordinates
    )
    print(f"   📏 Distance péage évité → Saint-Maurice : {distance_peages:.1f}km")
    
    # Service
    class MockORS:
        pass
    service = TollSegmentBuilder(MockORS())
    
    # Segments
    segments = service.build_intelligent_segments(
        start_coords=start_coords,
        end_coords=end_coords,
        all_tolls_on_route=all_tolls,
        selected_tolls=selected_tolls,
        route_coords=None
    )
    
    print(f"\n📋 Résultats de segmentation :")
    for i, segment in enumerate(segments, 1):
        print(f"   Segment {i} ({segment['type']}) : {segment['description']}")
        start_str = f"[{segment['start'][0]:.7f}, {segment['start'][1]:.7f}]"
        end_str = f"[{segment['end'][0]:.7f}, {segment['end'][1]:.7f}]"
        print(f"      📍 Départ : {start_str}")
        print(f"      📍 Arrivée : {end_str}")
        
        # Calcul distance dans le premier segment
        if i == 1 and segment['type'] == 'avoid_tolls':
            distance_to_target = analyzer.calculate_distance_km(
                segment['end'], 
                all_tolls[1].osm_coordinates  # Saint-Maurice
            )
            print(f"      📏 Distance entrée → Saint-Maurice : {distance_to_target:.1f}km")
            
            if distance_to_target > 3.0:
                print(f"      ✅ Bonne distance ! (> 3km)")
            else:
                print(f"      ⚠️ Distance encore trop courte (< 3km)")
    
    return segments


if __name__ == "__main__":
    segments = test_selestat_dijon_real()
