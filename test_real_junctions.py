"""
Test pour vérifier si le système trouve maintenant de vraies entrées d'autoroute.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.toll.new_segmentation.toll_segment_builder import TollSegmentBuilder
from src.cache.models.matched_toll import MatchedToll


def test_real_junctions():
    """Test pour vérifier l'utilisation des vraies jonctions."""
    
    # Coordonnées réelles Sélestat → Dijon
    start_coords = [7.448595, 48.262004]  
    end_coords = [5.037793, 47.317743]    
    
    # Route réelle avec plus de points pour améliorer la détection
    route_coords = [
        [7.448595, 48.262004],  # Sélestat
        [7.3, 48.1],            # Vers Colmar
        [7.1, 47.9],            # Colmar area
        [6.9, 47.8],            # Vers Besançon
        [6.8, 47.7],            # Fontaine Larivière area
        [6.7, 47.6],            # Entre péages
        [6.65, 47.5],           # Près Saint-Maurice
        [6.6, 47.45],           # Saint-Maurice area  
        [6.0, 47.4],            # Après Saint-Maurice
        [5.5, 47.35],           # Vers Dijon
        [5.2, 47.3],            # Dijon area
        [5.037793, 47.317743]   # Dijon final
    ]
    
    # Péages avec positions plus précises
    all_tolls = [
        MatchedToll(
            osm_id="fontaine_lariviere", 
            osm_name="Fontaine Larivière",
            osm_coordinates=[6.9816474, 47.6761296],  # Position de votre log
            csv_id=None,
            csv_name="Fontaine Larivière",
            csv_role='O',  # Système ouvert
            csv_coordinates=None,
            distance_m=0.0,
            confidence=1.0
        ),
        MatchedToll(
            osm_id="saint_maurice",
            osm_name="Péage de Saint-Maurice",
            osm_coordinates=[6.6712671, 47.4255066],  # Position de votre log
            csv_id=None,
            csv_name="Péage de Saint-Maurice",
            csv_role='F',  # Système fermé
            csv_coordinates=None,
            distance_m=0.0,
            confidence=1.0
        ),
        MatchedToll(
            osm_id="dijon_crimolois",
            osm_name="Péage de Dijon-Crimolois",
            osm_coordinates=[5.1380486, 47.2770761],  # Position de votre log
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
    
    print(f"\n🎯 Test jonctions réelles :")
    print(f"   Départ : {start_coords}")
    print(f"   Arrivée : {end_coords}")
    print(f"   Péages à éviter : {[t.effective_name for t in all_tolls if t not in selected_tolls]}")
    print(f"   Péages sélectionnés : {[t.effective_name for t in selected_tolls]}")
    
    # Service avec plus d'infos de debug
    class MockORS:
        pass
    
    service = TollSegmentBuilder(MockORS())
    
    print(f"\n🔧 Construction des segments avec junction_analyzer...")
    
    # Construire les segments (cela devrait maintenant utiliser les vraies junctions)
    segments = service.build_intelligent_segments(
        start_coords=start_coords,
        end_coords=end_coords,
        all_tolls_on_route=all_tolls,
        selected_tolls=selected_tolls,
        route_coords=route_coords  # Route plus détaillée
    )
    
    print(f"\n📊 Résultats :")
    print(f"   Nombre de segments : {len(segments)}")
    
    # Analyser le premier segment spécifiquement
    first_segment = segments[0] if segments else None
    if first_segment and first_segment['type'] == 'avoid_tolls':
        entrance_coords = first_segment['end']
        print(f"\n🎯 Analyse entrée stratégique :")
        print(f"   Coordonnées : {entrance_coords}")
        
        # Vérifier si c'est proche d'une position géométrique calculée vs une vraie junction
        expected_geometric = [6.795419219999999, 47.5257558]  # Position de votre log précédent
        
        distance_from_geometric = ((entrance_coords[0] - expected_geometric[0])**2 + 
                                 (entrance_coords[1] - expected_geometric[1])**2)**0.5
        
        if distance_from_geometric < 0.01:  # Très proche du calcul géométrique
            print(f"   ⚠️ Entrée géométrique (distance du calc géom: {distance_from_geometric:.6f})")
            print(f"   📍 Il s'agit probablement d'un point calculé, pas d'une vraie junction")
        else:
            print(f"   ✅ Entrée différente du calcul géométrique (distance: {distance_from_geometric:.6f})")
            print(f"   📍 Il s'agit possiblement d'une vraie junction d'autoroute")
    
    for i, segment in enumerate(segments, 1):
        print(f"\n   Segment {i} ({segment['type']}) : {segment['description']}")
        print(f"      📍 Départ : {segment['start']}")
        print(f"      📍 Arrivée : {segment['end']}")
    
    return segments


if __name__ == "__main__":
    segments = test_real_junctions()
