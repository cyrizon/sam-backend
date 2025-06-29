"""
Test simplifié du système de liaison par coordonnées
---------------------------------------------------

Test du nouveau système basé uniquement sur les coordonnées exactes.
"""

import os
import sys

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cache.v2.linking.coordinate_chain_builder import CoordinateChainBuilder
from src.cache.v2.parsers.motorway_segments_parser import MotorwaySegmentsParser
from src.cache.v2.models.link_types import LinkType


def test_coordinate_chain_builder():
    """Test du constructeur de chaînes par coordonnées."""
    print("🧪 Test du constructeur de chaînes par coordonnées")
    print("=" * 55)
    
    # Charger quelques segments indéterminés
    data_dir = "data"
    osm_dir = os.path.join(data_dir, "osm")
    indeterminates_path = os.path.join(osm_dir, "motorway_indeterminate.geojson")
    
    parser = MotorwaySegmentsParser()
    segments = parser.parse_segments(indeterminates_path, LinkType.INDETERMINATE)
    
    print(f"📥 Segments chargés: {len(segments)}")
    
    # Prendre seulement les 100 premiers pour le test
    test_segments = segments[:100]
    print(f"🔍 Test sur {len(test_segments)} segments")
    
    # Analyser quelques connexions
    print("\n📋 Analyse des connexions entre segments:")
    connections_found = 0
    for i, seg1 in enumerate(test_segments[:10]):
        for seg2 in test_segments:
            if seg1.way_id == seg2.way_id:
                continue
            
            # Test si fin de seg1 = début de seg2
            if (seg1.get_end_point()[0] == seg2.get_start_point()[0] and 
                seg1.get_end_point()[1] == seg2.get_start_point()[1]):
                print(f"   🔗 {seg1.way_id} fin → {seg2.way_id} début")
                connections_found += 1
                if connections_found >= 5:
                    break
        if connections_found >= 5:
            break
    
    # Construire les chaînes
    print(f"\n🏗️  Construction des chaînes...")
    builder = CoordinateChainBuilder()
    result = builder.build_chains(test_segments)
    
    # Analyser les résultats
    print(f"\n📊 Analyse des résultats:")
    stats = result.get_stats()
    print(f"   Chaînes créées: {stats['chains_count']}")
    print(f"   Segments chaînés: {stats['total_chained_segments']}")
    print(f"   Segments orphelins: {stats['orphaned_segments']}")
    
    if result.chains:
        print(f"\n📋 Détails de quelques chaînes:")
        for i, chain in enumerate(result.chains[:5]):
            way_ids = [seg.way_id for seg in chain.segments]
            print(f"   Chaîne {i+1} ({len(chain.segments)} segments): {' → '.join(way_ids)}")
    
    return len(result.chains) > 0


def test_specific_connection():
    """Test de la connexion spécifique mentionnée (way/85033 et way/4230917)."""
    print("\n🎯 Test de connexion spécifique")
    print("=" * 35)
    
    data_dir = "data"
    osm_dir = os.path.join(data_dir, "osm")
    indeterminates_path = os.path.join(osm_dir, "motorway_indeterminate.geojson")
    
    parser = MotorwaySegmentsParser()
    segments = parser.parse_segments(indeterminates_path, LinkType.INDETERMINATE)
    
    # Trouver les segments spécifiques
    seg_85033 = None
    seg_4230917 = None
    
    for segment in segments:
        if segment.way_id == "85033":
            seg_85033 = segment
        elif segment.way_id == "4230917":
            seg_4230917 = segment
        
        if seg_85033 and seg_4230917:
            break
    
    if seg_85033 and seg_4230917:
        print(f"✅ Segments trouvés:")
        print(f"   Way 85033 - Fin: {seg_85033.get_end_point()}")
        print(f"   Way 4230917 - Début: {seg_4230917.get_start_point()}")
        
        # Test de la connexion
        end_point = seg_85033.get_end_point()
        start_point = seg_4230917.get_start_point()
        
        if (abs(end_point[0] - start_point[0]) < 0.0000001 and 
            abs(end_point[1] - start_point[1]) < 0.0000001):
            print(f"✅ Connexion confirmée!")
            print(f"   Coordonnée commune: [{end_point[0]:.7f}, {end_point[1]:.7f}]")
        else:
            print(f"❌ Pas de connexion exacte")
            print(f"   Différence lon: {abs(end_point[0] - start_point[0])}")
            print(f"   Différence lat: {abs(end_point[1] - start_point[1])}")
    else:
        print(f"❌ Segments non trouvés:")
        print(f"   Way 85033: {'✅' if seg_85033 else '❌'}")
        print(f"   Way 4230917: {'✅' if seg_4230917 else '❌'}")


if __name__ == "__main__":
    print("🚀 Test du système de liaison par coordonnées")
    
    # Test de connexion spécifique
    test_specific_connection()
    
    # Test du constructeur de chaînes
    success = test_coordinate_chain_builder()
    
    if success:
        print("\n✅ Test réussi!")
    else:
        print("\n❌ Test échoué!")
