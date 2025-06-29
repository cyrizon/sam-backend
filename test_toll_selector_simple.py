#!/usr/bin/env python3
"""
Test du Toll Selector simplifié
===============================

Test de la création de segments selon la logique entrée/sortie.
"""

def test_toll_selector_simple():
    """Test de la logique simplifiée du toll selector."""
    print("🧪 Test du Toll Selector simplifié...")
    
    try:
        from src.services.toll.route_optimization.toll_analysis.toll_selector import TollSelector
        from src.cache.v2.models.complete_motorway_link import CompleteMotorwayLink
        from src.cache.v2.models.link_types import LinkType
        from src.cache.v2.models.toll_booth_station import TollBoothStation
        
        print("✅ Imports réussis")
        
        # Mock des éléments sélectionnés
        # Simuler : [départ, tollboothstation, exit, entry, tollboothstation, arrivée]
        
        # TollBoothStation mock
        toll1 = TollBoothStation(
            osm_id="TOLL_001",
            name="Péage A6 Nord",
            coordinates=[2.3, 48.5],
            operator="ASF",
            operator_ref=None,
            highway_ref="A6",
            properties={}
        )
        
        toll2 = TollBoothStation(
            osm_id="TOLL_002", 
            name="Péage A6 Sud",
            coordinates=[2.2, 44.0],
            operator="ASF",
            operator_ref=None,
            highway_ref="A6",
            properties={}
        )
        
        # CompleteMotorwayLink EXIT mock
        exit_link = CompleteMotorwayLink(
            link_id="EXIT_001",
            link_type=LinkType.EXIT,
            segments=[]  # Simplifié pour le test
        )
        # Simuler les coordonnées
        exit_link.start_coordinates = [2.25, 47.0]
        exit_link.end_coordinates = [2.2, 46.8]
        
        # CompleteMotorwayLink ENTRY mock  
        entry_link = CompleteMotorwayLink(
            link_id="ENTRY_001",
            link_type=LinkType.ENTRY,
            segments=[]  # Simplifié pour le test
        )
        # Simuler les coordonnées
        entry_link.start_coordinates = [2.15, 45.5]
        entry_link.end_coordinates = [2.18, 45.3]
        
        # Initialisation
        selector = TollSelector()
        
        print("✅ Initialisation réussie")
        
        # Points de départ et arrivée
        start_point = [2.3522, 48.8566]  # Paris
        end_point = [2.2945, 43.2951]    # Toulouse
        
        # Éléments sélectionnés dans l'ordre
        selected_tolls = [toll1, exit_link, entry_link, toll2]
        
        print(f"\n📋 Test création structure avec {len(selected_tolls)} éléments")
        print("   Séquence : TollBooth → EXIT → ENTRY → TollBooth")
        
        # Créer la structure de segments
        segments = selector._create_segments_structure(
            selected_tolls, start_point, end_point
        )
        
        print(f"\n📊 Résultats :")
        print(f"   ✅ {len(segments)} segments créés")
        
        for i, segment in enumerate(segments):
            start = segment['start_point']
            end = segment['end_point'] 
            has_toll = segment['has_toll']
            reason = segment['segment_reason']
            
            print(f"   📍 Segment {i+1}: {start} → {end}")
            print(f"      {'💰 Avec péage' if has_toll else '🚫 Sans péage'} - {reason}")
        
        # Vérifications selon la logique
        expected_toll_flags = [
            True,   # Départ → TollBooth (avec péage)
            True,   # TollBooth → EXIT end (avec péage, sortie autoroute)
            False,  # EXIT end → ENTRY start (sans péage, hors autoroute) 
            True,   # ENTRY start → TollBooth (avec péage, sur autoroute)
            True    # TollBooth → Arrivée (avec péage)
        ]
        
        assert len(segments) == len(expected_toll_flags), f"Attendu {len(expected_toll_flags)} segments, reçu {len(segments)}"
        
        for i, (segment, expected) in enumerate(zip(segments, expected_toll_flags)):
            actual = segment['has_toll']
            assert actual == expected, f"Segment {i+1}: attendu has_toll={expected}, reçu {actual}"
        
        print(f"   ✅ Vérifications logique réussies")
        
        # Test cas simple : juste des péages normaux
        print(f"\n📋 Test cas simple : péages seulement")
        
        simple_tolls = [toll1, toll2]
        simple_segments = selector._create_segments_structure(
            simple_tolls, start_point, end_point
        )
        
        print(f"   ✅ {len(simple_segments)} segments simples créés")
        assert len(simple_segments) == 3, "Devrait avoir 3 segments : départ→toll1, toll1→toll2, toll2→arrivée"
        assert all(seg['has_toll'] for seg in simple_segments), "Tous les segments devraient avoir des péages"
        
        print("\n🎉 Test du Toll Selector simplifié réussi!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans le test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_toll_selector_simple()
