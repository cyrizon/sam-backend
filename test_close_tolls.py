"""
Test spécifique pour valider la logique avec des péages rapprochés (comme Sélestat-Dijon).
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.toll.new_segmentation.toll_segment_builder import TollSegmentBuilder
from src.cache.models.matched_toll import MatchedToll


def test_close_tolls():
    """Test avec des péages très rapprochés (comme la réalité)."""
    
    # Coordonnées réelles approximatives Sélestat → Dijon
    start_coords = [7.448595, 48.262004]  # Sélestat
    end_coords = [5.037793, 47.317743]    # Dijon
    
    # Route simulée
    route_coords = [
        [7.448595, 48.262004],  # Départ - Sélestat
        [7.1, 47.9],            # Vers Colmar
        [6.8, 47.7],            # Avant Mulhouse
        [6.6, 47.5],            # Région Besançon 
        [6.0, 47.4],            # Après Besançon
        [5.5, 47.35],           # Avant Dijon
        [5.037793, 47.317743]   # Arrivée - Dijon
    ]
    
    # Péages simulés avec noms réels et positions approximatives
    all_tolls = [
        MatchedToll(
            osm_id="toll_besancon",
            osm_name="Péage de Besançon",
            osm_coordinates=[6.6, 47.5],  # Près Besançon
            csv_id=None,
            csv_name="Péage de Besançon",
            csv_role='O',
            csv_coordinates=None,
            distance_m=0.0,
            confidence=1.0
        ),
        MatchedToll(
            osm_id="toll_saint_maurice",
            osm_name="Péage de Saint-Maurice",
            osm_coordinates=[6.67, 47.425],  # Plus proche du précédent
            csv_id=None,
            csv_name="Péage de Saint-Maurice",
            csv_role='O',
            csv_coordinates=None,
            distance_m=0.0,
            confidence=1.0
        ),
        MatchedToll(
            osm_id="toll_dijon_crimolois",
            osm_name="Péage de Dijon-Crimolois", 
            osm_coordinates=[5.1380486, 47.2770761],  # Dijon
            csv_id=None,
            csv_name="Péage de Dijon-Crimolois",
            csv_role='O',
            csv_coordinates=None,
            distance_m=0.0,
            confidence=1.0
        )
    ]
    
    # Scénario : on veut éviter Besançon, prendre Saint-Maurice et Dijon
    selected_tolls = [all_tolls[1], all_tolls[2]]  # Saint-Maurice + Dijon
    
    print(f"\n🧪 Test péages rapprochés :")
    print(f"   Départ : {start_coords}")
    print(f"   Arrivée : {end_coords}")
    print(f"   Tous les péages : {[t.effective_name for t in all_tolls]}")
    print(f"   Péages sélectionnés : {[t.effective_name for t in selected_tolls]}")
    print(f"   Péages à éviter : {[t.effective_name for t in all_tolls if t not in selected_tolls]}")
    
    # Distances entre péages
    for i, toll in enumerate(all_tolls[:-1]):
        next_toll = all_tolls[i+1]
        from src.services.toll.new_segmentation.segment_building.highway_entrance_analyzer import HighwayEntranceAnalyzer
        analyzer = HighwayEntranceAnalyzer(None)
        distance = analyzer.calculate_distance_km(toll.osm_coordinates, next_toll.osm_coordinates)
        print(f"   📏 {toll.effective_name} → {next_toll.effective_name} : {distance:.1f}km")
    
    # Créer le service
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
    
    return segments


if __name__ == "__main__":
    segments = test_close_tolls()
