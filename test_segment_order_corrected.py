"""
Test de l'ordre des segments après corrections.
"""

import sys
sys.path.append('.')

from src.services.toll.route_optimization.main.intelligent_optimizer import IntelligentOptimizer

def test_segment_order():
    """Test l'ordre correct des segments."""
    
    # Mock du service ORS
    class MockORS:
        def get_route_with_coordinates(self, *args, **kwargs):
            return {
                'route_coords': [[7.448405, 48.261682], [3.11506, 45.784359]],
                'duration': 325.7 * 60,  # en secondes
                'distance': 576.4 * 1000,  # en mètres
                'geometry': 'mock_geometry'
            }
    
    # Initialiser l'optimiseur
    ors_service = MockORS()
    optimizer = IntelligentOptimizer(ors_service)
    
    # Coordonnées du test (Sélestat → Besançon)
    coordinates = [
        [7.448405, 48.261682],  # Sélestat
        [3.11506, 45.784359]    # Besançon (approximatif)
    ]
    
    print("🧪 Test de l'ordre des segments")
    print(f"   Route : Sélestat → Besançon")
    print(f"   Objectif : 2 péages")
    
    # Lancer l'optimisation
    result = optimizer.find_optimized_route(coordinates, 2, 'count')
    
    if result and result.get('segments'):
        segments = result['segments']
        print(f"\n📊 Résultat : {len(segments)} segments")
        
        for i, segment in enumerate(segments):
            has_toll = segment.get('has_toll', False)
            reason = segment.get('segment_reason', 'Inconnu')
            start = segment.get('start_point', [0, 0])
            end = segment.get('end_point', [0, 0])
            
            toll_status = '🚫 SANS péage' if not has_toll else '💰 AVEC péages'
            print(f"   Segment {i+1}: {toll_status}")
            print(f"      📍 {start} → {end}")
            print(f"      💡 {reason}")
        
        # Vérification de l'ordre attendu
        print(f"\n✅ Vérification de l'ordre :")
        if len(segments) >= 2:
            first_toll = segments[0].get('has_toll', False)
            second_toll = segments[1].get('has_toll', False)
            
            if not first_toll and second_toll:
                print(f"   ✅ CORRECT : Segment 1 SANS péage, Segment 2 AVEC péages")
                return True
            else:
                print(f"   ❌ INCORRECT : Segment 1 {first_toll}, Segment 2 {second_toll}")
                print(f"      Attendu : Segment 1 False, Segment 2 True")
                return False
        else:
            print(f"   ⚠️ Pas assez de segments pour vérifier l'ordre")
            return False
    else:
        print(f"   ❌ Aucun résultat ou segments")
        return False

if __name__ == "__main__":
    success = test_segment_order()
    print(f"\n🏁 Test {'réussi' if success else 'échoué'}")
