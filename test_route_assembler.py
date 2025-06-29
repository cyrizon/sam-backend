#!/usr/bin/env python3
"""
Test du Route Assembler adapté
==============================

Test de l'assemblage de routes avec les données du segment_calculator.
"""

def test_route_assembler():
    """Test de l'assembleur de routes."""
    print("🧪 Test du Route Assembler adapté...")
    
    try:
        from src.services.toll.route_optimization.assembly.route_assembler import RouteAssembler
        
        print("✅ Import réussi")
        
        # Segments simulés comme retournés par segment_calculator
        segments_data = [
            {
                'segment_id': 0,
                'segment_type': 'with_tolls',
                'start_point': [2.3522, 48.8566],  # Paris
                'end_point': [2.1, 47.5],          # Péage X
                'has_tolls': True,
                'calculation_method': 'with_tolls',
                
                # Données extraites d'ORS
                'distance_m': 750.0,
                'duration_s': 120.0,
                'distance_km': 0.75,
                'duration_min': 2.0,
                
                # Géométrie
                'coordinates': [
                    [2.3522, 48.8566],
                    [2.3, 48.0],
                    [2.1, 47.5]
                ],
                
                # Segments détaillés avec instructions
                'segments_detail': [{
                    'distance': 750.0,
                    'duration': 120.0,
                    'steps': [
                        {
                            'instruction': 'Head south on A6',
                            'name': 'A6',
                            'distance': 500.0,
                            'duration': 80.0
                        },
                        {
                            'instruction': 'Continue on A6',
                            'name': 'A6',
                            'distance': 250.0,
                            'duration': 40.0
                        }
                    ]
                }]
            },
            {
                'segment_id': 1,
                'segment_type': 'with_tolls',
                'start_point': [2.1, 47.5],        # Péage X
                'end_point': [2.0, 46.5],          # Sortie X
                'has_tolls': True,
                'calculation_method': 'with_tolls',
                
                'distance_m': 890.0,
                'duration_s': 150.0,
                'distance_km': 0.89,
                'duration_min': 2.5,
                
                'coordinates': [
                    [2.1, 47.5],
                    [2.05, 47.0],
                    [2.0, 46.5]
                ],
                
                'segments_detail': [{
                    'distance': 890.0,
                    'duration': 150.0,
                    'steps': [
                        {
                            'instruction': 'Continue on A6',
                            'name': 'A6',
                            'distance': 890.0,
                            'duration': 150.0
                        }
                    ]
                }]
            },
            {
                'segment_id': 2,
                'segment_type': 'no_tolls',
                'start_point': [2.0, 46.5],        # Sortie X
                'end_point': [2.2945, 43.2951],    # Toulouse
                'has_tolls': False,
                'calculation_method': 'avoid_tolls',
                
                'distance_m': 1200.0,
                'duration_s': 200.0,
                'distance_km': 1.2,
                'duration_min': 3.3,
                
                'coordinates': [
                    [2.0, 46.5],
                    [2.1, 45.0],
                    [2.2945, 43.2951]
                ],
                
                'segments_detail': [{
                    'distance': 1200.0,
                    'duration': 200.0,
                    'steps': [
                        {
                            'instruction': 'Exit highway',
                            'name': 'Local Road',
                            'distance': 1200.0,
                            'duration': 200.0
                        }
                    ]
                }]
            }
        ]
        
        print(f"\n📋 Test assemblage de {len(segments_data)} segments")
        
        # Assembler la route finale
        result = RouteAssembler.assemble_final_route(
            segments=segments_data,
            target_tolls=2,
            selected_tolls=[
                {'name': 'Péage A6 Nord'},
                {'name': 'Péage A6 Sud'}
            ]
        )
        
        print(f"\n📊 Résultats :")
        print(f"   ✅ Route assemblée")
        print(f"   📏 Distance totale: {result['distance']/1000:.1f} km")
        print(f"   ⏱️ Durée totale: {result['duration']/60:.1f} min")
        print(f"   📍 Instructions: {len(result['instructions'])} étapes")
        print(f"   🏗️ Segments: {result['segments']['count']}")
        print(f"   💰 Segments avec péages: {result['segments']['toll_segments']}")
        print(f"   🚫 Segments sans péages: {result['segments']['free_segments']}")
        
        # Vérifications
        assert result['distance'] == 2840.0, f"Distance attendue 2840m, reçue {result['distance']}m"
        assert result['duration'] == 470.0, f"Durée attendue 470s, reçue {result['duration']}s"
        assert len(result['instructions']) > 0, "Instructions devraient être présentes"
        assert result['segments']['count'] == 3, "Devrait avoir 3 segments"
        assert result['segments']['toll_segments'] == 2, "Devrait avoir 2 segments avec péages"
        assert result['segments']['free_segments'] == 1, "Devrait avoir 1 segment sans péages"
        
        # Vérifier la géométrie assemblée
        route_coords = result['route']['features'][0]['geometry']['coordinates']
        print(f"   🗺️ Coordonnées assemblées: {len(route_coords)} points")
        
        # Vérifications de cohérence
        assert len(route_coords) > 5, "Devrait avoir plus de 5 points de coordonnées"
        assert route_coords[0] == [2.3522, 48.8566], "Premier point devrait être Paris"
        assert route_coords[-1] == [2.2945, 43.2951], "Dernier point devrait être Toulouse"
        
        print(f"   ✅ Vérifications réussies")
        
        print("\n🎉 Test du Route Assembler réussi!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans le test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_route_assembler()
