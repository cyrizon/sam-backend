#!/usr/bin/env python3
"""
Test du Segment Creator simplifié
================================

Test de la création de segments selon le format attendu.
"""

def test_segment_creator():
    """Test basique du créateur de segments."""
    print("🧪 Test du Segment Creator simplifié...")
    
    try:
        from src.services.toll.route_optimization.segmentation.segment_creator import SegmentCreator
        
        print("✅ Import réussi")
        
        # Initialisation
        creator = SegmentCreator()
        
        # Coordonnées de test
        coordinates = [
            [2.3522, 48.8566],  # Paris (départ)
            [2.2945, 43.2951]   # Toulouse (arrivée)
        ]
        
        print("✅ Initialisation réussie")
        
        # Test 1: Pas de péages
        print("\n📋 Test 1: Pas de péages")
        
        result1 = creator.create_optimized_segments(
            coordinates=coordinates,
            selected_tolls=[],
            identification_result={},
            selection_result={}
        )
        
        print(f"   ✅ Résultat: {len(result1)} segment(s)")
        print(f"   📊 Type: {result1[0]['segment_type']}")
        print(f"   📊 Éviter péages: {result1[0]['avoid_tolls']}")
        
        # Test 2: Avec segments définis dans selection_result
        print("\n📋 Test 2: Segments définis")
        
        selection_result_mock = {
            'segments': [
                {
                    'start_point': [2.3522, 48.8566],  # Départ
                    'end_point': [2.1, 47.5],          # Péage X
                    'has_toll': True,
                    'toll_info': {'name': 'Péage X', 'type': 'ouvert'}
                },
                {
                    'start_point': [2.1, 47.5],        # Péage X
                    'end_point': [2.0, 46.5],          # Sortie X
                    'has_toll': True,
                    'toll_info': {'name': 'Section X', 'type': 'fermé'}
                },
                {
                    'start_point': [2.0, 46.5],        # Sortie X
                    'end_point': [2.2945, 43.2951],    # Arrivée
                    'has_toll': False,
                    'toll_info': {}
                }
            ]
        }
        
        result2 = creator.create_optimized_segments(
            coordinates=coordinates,
            selected_tolls=[{'name': 'Test'}],  # Juste pour déclencher le traitement
            identification_result={},
            selection_result=selection_result_mock
        )
        
        print(f"   ✅ Résultat: {len(result2)} segment(s)")
        for i, segment in enumerate(result2):
            has_toll = not segment['avoid_tolls']
            print(f"   📊 Segment {i}: {'avec' if has_toll else 'sans'} péage")
        
        # Test 3: Fallback simple
        print("\n📋 Test 3: Fallback simple")
        
        selected_tolls_mock = [
            {'name': 'Péage A', 'coordinates': [2.1, 47.5]},
            {'name': 'Péage B', 'coordinates': [2.0, 46.5]}
        ]
        
        result3 = creator.create_optimized_segments(
            coordinates=coordinates,
            selected_tolls=selected_tolls_mock,
            identification_result={},
            selection_result={}  # Pas de segments définis
        )
        
        print(f"   ✅ Résultat: {len(result3)} segment(s)")
        print(f"   📊 Type: {result3[0]['segment_type']}")
        print(f"   📊 Péages forcés: {len(result3[0]['force_tolls'])}")
        
        print("\n🎉 Tests du Segment Creator réussis!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur dans le test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_segment_creator()
