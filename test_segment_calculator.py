#!/usr/bin/env python3
"""
Test du Segment Calculator simplifié
===================================

Test du calcul de segments via ORS.
"""

def test_segment_calculator():
    """Test basique du calculateur de segments."""
    print("🧪 Test du Segment Calculator simplifié...")
    
    try:
        from src.services.toll.route_optimization.segmentation.segment_calculator import SegmentCalculator
        from src.services.ors_service import ORSService
        
        print("✅ Imports réussis")
        
        # Mock du service ORS pour les tests avec données réalistes
        class MockORSService:
            def get_route_avoid_tollways(self, coordinates):
                print(f"     🚫 Mock: Éviter péages {coordinates[0]} -> {coordinates[1]}")
                return {
                    "type": "FeatureCollection",
                    "features": [{
                        "type": "Feature",
                        "properties": {
                            "segments": [{
                                "distance": 890.6,
                                "duration": 189.6,
                                "steps": []
                            }],
                            "extras": {
                                "tollways": {
                                    "values": [[0, 25, 0]],
                                    "summary": [{"value": 0, "distance": 890.6, "amount": 100}]
                                }
                            },
                            "summary": {"distance": 890.6, "duration": 189.6}
                        },
                        "geometry": {
                            "coordinates": [coordinates[0], coordinates[1]],
                            "type": "LineString"
                        }
                    }]
                }
            
            def get_base_route(self, coordinates, include_tollways=True):
                print(f"     💰 Mock: Avec péages {coordinates[0]} -> {coordinates[1]}")
                return {
                    "type": "FeatureCollection", 
                    "features": [{
                        "type": "Feature",
                        "properties": {
                            "segments": [{
                                "distance": 750.0,
                                "duration": 120.0,
                                "steps": []
                            }],
                            "extras": {
                                "tollways": {
                                    "values": [[0, 15, 1]],
                                    "summary": [{"value": 1, "distance": 500.0, "amount": 66.7}]
                                }
                            },
                            "summary": {"distance": 750.0, "duration": 120.0}
                        },
                        "geometry": {
                            "coordinates": [coordinates[0], coordinates[1]],
                            "type": "LineString"
                        }
                    }]
                }
        
        # Initialisation
        mock_ors = MockORSService()
        calculator = SegmentCalculator(mock_ors)
        
        print("✅ Initialisation réussie")
        
        # Test avec segments créés par segment_creator
        segments_config = [
            {
                'segment_id': 0,
                'segment_type': 'with_tolls',
                'start_point': [2.3522, 48.8566],  # Paris
                'end_point': [2.1, 47.5],          # Péage X
                'avoid_tolls': False,  # Avec péages
                'force_tolls': [{'name': 'Péage X'}]
            },
            {
                'segment_id': 1,
                'segment_type': 'with_tolls',
                'start_point': [2.1, 47.5],        # Péage X
                'end_point': [2.0, 46.5],          # Sortie X
                'avoid_tolls': False,  # Avec péages
                'force_tolls': [{'name': 'Section X'}]
            },
            {
                'segment_id': 2,
                'segment_type': 'no_tolls',
                'start_point': [2.0, 46.5],        # Sortie X
                'end_point': [2.2945, 43.2951],    # Toulouse
                'avoid_tolls': True,   # Sans péages
                'force_tolls': []
            }
        ]
        
        print(f"\n📋 Test calcul de {len(segments_config)} segments")
        
        # Calculer les routes pour chaque segment
        result = calculator.calculate_segments_routes(segments_config, {})
        
        print(f"\n📊 Résultats :")
        print(f"   ✅ {len(result)} segments calculés")
        
        for i, segment in enumerate(result):
            method = segment.get('calculation_method', 'unknown')
            has_tolls = segment.get('has_tolls', False)
            distance_km = segment.get('distance_km', 0)
            duration_min = segment.get('duration_min', 0)
            tollways_info = segment.get('tollways_info', [])
            
            print(f"   📍 Segment {i}: {method} ({'avec' if has_tolls else 'sans'} péages)")
            print(f"      📏 Distance: {distance_km} km, Durée: {duration_min} min")
            print(f"      🛣️ Info péages: {len(tollways_info)} entrée(s)")
        
        # Vérifications
        assert len(result) == 3, f"Attendu 3 segments, reçu {len(result)}"
        assert result[0]['has_tolls'] == True, "Segment 0 devrait avoir des péages"
        assert result[1]['has_tolls'] == True, "Segment 1 devrait avoir des péages"
        assert result[2]['has_tolls'] == False, "Segment 2 ne devrait pas avoir de péages"
        
        # Vérifications des données extraites
        assert result[0]['distance_km'] > 0, "Distance devrait être > 0"
        assert result[0]['duration_min'] > 0, "Durée devrait être > 0"
        assert 'geometry' in result[0], "Géométrie devrait être présente"
        
        print(f"   ✅ Vérifications réussies")
        
        print("\n🎉 Test du Segment Calculator réussi!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans le test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_segment_calculator()
