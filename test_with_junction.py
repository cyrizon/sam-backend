"""
Test avec mock OSM parser pour tester la logique junction_analyzer.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.toll.new_segmentation.toll_segment_builder import TollSegmentBuilder
from src.services.toll.new_segmentation.toll_matcher import MatchedToll


class MockOSMParser:
    """Mock OSM parser pour le test."""
    def __init__(self):
        # Mock des motorway_junctions avec quelques entrées simulées
        self.motorway_junctions = [
            {
                'id': 'junction_1',
                'name': 'Sortie 12 - Colmar Sud',
                'ref': '12',
                'coordinates': [7.2, 48.0],  # Entre Sélestat et Saint-Maurice
                'link_coordinates': [7.2, 48.0],
                'highway': 'motorway_junction'
            },
            {
                'id': 'junction_2', 
                'name': 'Sortie 15 - Mulhouse Ouest',
                'ref': '15',
                'coordinates': [7.0, 47.85],  # Après Fontaine Larivière
                'link_coordinates': [7.0, 47.85],
                'highway': 'motorway_junction'
            },
            {
                'id': 'junction_3',
                'name': 'Sortie 18 - Belfort',
                'ref': '18', 
                'coordinates': [6.85, 47.7],  # Avant Saint-Maurice
                'link_coordinates': [6.85, 47.7],
                'highway': 'motorway_junction'
            }
        ]


def test_with_junction_analyzer():
    """Test avec junction_analyzer activé."""
    
    # Coordonnées exactes de votre exemple
    start_coords = [7.448595, 48.262004]  # Sélestat
    end_coords = [5.037793, 47.317743]    # Dijon
    
    # Route simulée avec plus de détails
    route_coords = [
        [7.448595, 48.262004],  # Départ - Sélestat
        [7.3, 48.1],            # Point 1
        [7.1, 47.9],            # Point 2
        [6.9, 47.8],            # Point 3 - Région Fontaine Larivière
        [6.8, 47.7],            # Point 4
        [6.7, 47.6],            # Point 5
        [6.6, 47.5],            # Point 6 - Région Saint-Maurice
        [6.0, 47.4],            # Point 7
        [5.5, 47.35],           # Point 8
        [5.2, 47.3],            # Point 9 - Région Dijon
        [5.037793, 47.317743]   # Arrivée - Dijon
    ]
    
    # Péages simulés
    all_tolls = [
        MatchedToll(
            osm_id="toll_fontaine",
            osm_name="Fontaine Larivière",
            osm_coordinates=[6.9816474, 47.6761296],  # Coordonnées exactes de votre log
            csv_id=None,
            csv_name="Fontaine Larivière",
            csv_role='O',  # Système ouvert
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
            csv_role='F',  # Système fermé
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
            csv_role='F',  # Système fermé
            csv_coordinates=None,
            distance_m=0.0,
            confidence=1.0
        )
    ]
    
    # Scénario : éviter Fontaine Larivière (ouvert), prendre les 2 fermés
    selected_tolls = [all_tolls[1], all_tolls[2]]  # Saint-Maurice + Dijon
    
    print(f"\n🧪 Test avec junction_analyzer simulé :")
    print(f"   Départ : {start_coords}")
    print(f"   Arrivée : {end_coords}")
    print(f"   Tous les péages : {[t.effective_name for t in all_tolls]}")
    print(f"   Péages sélectionnés : {[t.effective_name for t in selected_tolls]}")
    print(f"   Péages à éviter : {[t.effective_name for t in all_tolls if t not in selected_tolls]}")
    
    # Service avec mock OSM parser
    class MockORS:
        pass
    
    service = TollSegmentBuilder(MockORS())
    
    # Mock OSM parser
    mock_osm_parser = MockOSMParser()
    
    # Construire les segments AVEC osm_parser
    segments = service.build_intelligent_segments(
        start_coords=start_coords,
        end_coords=end_coords,
        all_tolls_on_route=all_tolls,
        selected_tolls=selected_tolls,
        osm_parser=mock_osm_parser,  # Ici on fournit le mock parser !
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
    segments = test_with_junction_analyzer()
