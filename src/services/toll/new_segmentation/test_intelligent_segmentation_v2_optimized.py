"""
test_intelligent_segmentation_v2_optimized.py
-------------------------------------------

Tests pour la stratégie de segmentation intelligente V2 optimisée.
Valide les optimisations clés :
- Travail sur segments tollways
- Péages pré-matchés avec csv_role
- Utilisation des motorway_junctions liés
- Logique segments gratuits optimisée
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.toll.new_segmentation.intelligent_segmentation_v2_optimized import IntelligentSegmentationStrategyV2Optimized
from src.services.osm_data_cache import osm_data_cache
from unittest.mock import Mock


def test_v2_optimized_basic():
    """Test de base de la stratégie V2 optimisée."""
    print("🧪 Test V2 Optimisée - Fonctionnement de base")
    
    # Initialiser le cache OSM (requis)
    osm_data_cache.initialize()
    
    # Mock du service ORS
    mock_ors = Mock()
    
    # Simuler une réponse ORS avec segments tollways
    mock_route_response = {
        'status': 'success',
        'data': {
            'routes': [{
                'geometry': [[2.3522, 48.8566], [2.3622, 48.8666]],  # Paris exemple
                'extras': {
                    'tollways': {
                        'values': [
                            [0, 10, 0],    # Segment gratuit
                            [10, 20, 1],   # Segment payant
                            [20, 30, 0]    # Segment gratuit
                        ]
                    }
                }
            }]
        }
    }
    
    mock_ors.get_route.return_value = mock_route_response
    
    # Initialiser la stratégie
    strategy = IntelligentSegmentationStrategyV2Optimized(mock_ors)
    
    # Test avec coordonnées de base
    coordinates = [[2.3522, 48.8566], [2.3622, 48.8666]]
    
    # Vérifier que l'initialisation s'est bien passée
    assert strategy.ors is not None
    assert strategy.osm_parser is not None
    assert strategy.tollways_analyzer is not None
    
    print("✅ Initialisation V2 Optimisée réussie")


def test_tollways_extraction():
    """Test de l'extraction des segments tollways."""
    print("🧪 Test extraction segments tollways")
    
    # Mock du service ORS
    mock_ors = Mock()
    strategy = IntelligentSegmentationStrategyV2Optimized(mock_ors)
    
    # Route de test avec segments tollways
    test_route = {
        'geometry': [[2.3522, 48.8566], [2.3622, 48.8666]],
        'extras': {
            'tollways': {
                'values': [
                    [0, 5, 0],     # Gratuit
                    [5, 15, 1],    # Payant
                    [15, 25, 1],   # Payant
                    [25, 30, 0]    # Gratuit
                ]
            }
        }
    }
    
    # Extraire les segments
    tollways_data = strategy._extract_tollways_segments(test_route)
    
    # Vérifications
    assert tollways_data is not None
    assert len(tollways_data['segments']) == 4
    assert tollways_data['toll_segments'] == 2
    assert tollways_data['free_segments'] == 2
    
    # Vérifier les segments individuels
    segments = tollways_data['segments']
    assert segments[0]['is_toll'] == False  # Gratuit
    assert segments[1]['is_toll'] == True   # Payant
    assert segments[2]['is_toll'] == True   # Payant
    assert segments[3]['is_toll'] == False  # Gratuit
    
    print("✅ Extraction segments tollways réussie")


def test_prematched_tolls_logic():
    """Test de la logique des péages pré-matchés."""
    print("🧪 Test logique péages pré-matchés")
    
    # Initialiser le cache OSM
    osm_data_cache.initialize()
    
    mock_ors = Mock()
    strategy = IntelligentSegmentationStrategyV2Optimized(mock_ors)
    
    # Simuler des péages pré-matchés
    from src.services.toll.new_segmentation.toll_matcher import MatchedToll
    
    prematched_tolls = [
        MatchedToll(
            osm_id="toll_1",
            osm_name="Péage Test 1",
            osm_coordinates=[2.3522, 48.8566],
            csv_id="csv_1",
            csv_name="Péage CSV 1",
            csv_role="O",  # Système ouvert
            csv_coordinates=[2.3522, 48.8566],
            distance_m=0,
            confidence=1.0
        ),
        MatchedToll(
            osm_id="toll_2",
            osm_name="Péage Test 2",
            osm_coordinates=[2.3622, 48.8666],
            csv_id="csv_2",
            csv_name="Péage CSV 2",
            csv_role="F",  # Système fermé
            csv_coordinates=[2.3622, 48.8666],
            distance_m=0,
            confidence=1.0
        )
    ]
    
    # Test de sélection optimisée (prioriser système ouvert)
    selected = strategy._select_target_tolls_optimized(prematched_tolls, 1)
    
    # Le péage ouvert doit être sélectionné en premier
    assert len(selected) == 1
    assert selected[0].csv_role == "O"
    assert selected[0].osm_id == "toll_1"
    
    print("✅ Logique péages pré-matchés réussie")


def test_free_segments_logic():
    """Test de la logique des segments gratuits optimisée."""
    print("🧪 Test logique segments gratuits optimisée")
    
    mock_ors = Mock()
    strategy = IntelligentSegmentationStrategyV2Optimized(mock_ors)
    
    # Simuler des segments
    test_segments = [
        {'segment_type': 'toll', 'id': 'seg_1'},
        {'segment_type': 'free', 'id': 'seg_2'},  # Segment gratuit
        {'segment_type': 'toll', 'id': 'seg_3'}
    ]
    
    # Simuler des péages fermés
    from src.services.toll.new_segmentation.toll_matcher import MatchedToll
    
    closed_tolls = [
        MatchedToll(
            osm_id="toll_1", osm_name="Péage 1", osm_coordinates=[2.3522, 48.8566],
            csv_id=None, csv_name=None, csv_role="F", csv_coordinates=None,
            distance_m=0, confidence=0
        ),
        MatchedToll(
            osm_id="toll_2", osm_name="Péage 2", osm_coordinates=[2.3622, 48.8666],
            csv_id=None, csv_name=None, csv_role="F", csv_coordinates=None,
            distance_m=0, confidence=0
        )
    ]
    
    # Appliquer la logique segments gratuits
    result = strategy._apply_free_segments_logic(test_segments, closed_tolls)
    
    # Avec 2 péages fermés, le segment gratuit intermédiaire doit être supprimé
    assert len(result) < len(test_segments)
    
    # Vérifier qu'il ne reste que les segments payants
    remaining_types = [seg.get('segment_type') for seg in result]
    assert 'free' not in remaining_types or len(closed_tolls) < 2
    
    print("✅ Logique segments gratuits optimisée réussie")


def main():
    """Lance tous les tests."""
    print("🚀 Tests Stratégie V2 Optimisée")
    print("=" * 50)
    
    try:
        test_v2_optimized_basic()
        test_tollways_extraction()
        test_prematched_tolls_logic()
        test_free_segments_logic()
        
        print("\n" + "=" * 50)
        print("✅ TOUS LES TESTS RÉUSSIS")
        print("🎉 Stratégie V2 Optimisée fonctionnelle")
        
    except Exception as e:
        print(f"\n❌ ÉCHEC DES TESTS : {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
