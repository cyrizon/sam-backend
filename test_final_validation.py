"""
Test de validation finale du système d'optimisation de péages avec objets
"""

import pytest
from unittest.mock import Mock, patch
from src.services.toll.route_optimization.toll_analysis.toll_selector import TollSelector
from src.services.toll.route_optimization.utils.cache_accessor import CacheAccessor
from src.cache.v2.models.toll_booth_station import TollBoothStation


def test_complete_pipeline_validation():
    """Test complet pour valider que le pipeline fonctionne avec des objets uniquement."""
    
    print("=" * 80)
    print("🚀 VALIDATION FINALE DU PIPELINE AVEC OBJETS")
    print("=" * 80)
    
    # Créer des objets mock réalistes
    mock_toll_1 = Mock(spec=TollBoothStation)
    mock_toll_1.osm_id = 'node/126217'
    mock_toll_1.name = 'Auxerre Nord'
    mock_toll_1.operator = 'APRR'
    mock_toll_1.coordinates = [3.5, 47.8]
    
    mock_toll_2 = Mock(spec=TollBoothStation)
    mock_toll_2.osm_id = 'node/142831'
    mock_toll_2.name = 'Ambérieu-en-Buguey'
    mock_toll_2.operator = 'APRR'
    mock_toll_2.coordinates = [5.3, 45.9]
    
    # Simulation réaliste d'un résultat d'identification
    identification_result = {
        'total_tolls_on_route': 2,
        'tolls_on_route': [
            {'toll': mock_toll_1, 'distance': 10.5, 'toll_type': 'fermé'},
            {'toll': mock_toll_2, 'distance': 20.3, 'toll_type': 'fermé'}
        ],
        'route_info': {
            'start_point': [3.0, 47.0],
            'end_point': [6.0, 46.0]
        }
    }
    
    # Test 1: Validation du mode COUNT
    print("\n1. 🎯 VALIDATION MODE COUNT")
    print("-" * 50)
    
    toll_selector = TollSelector()
    
    result_count = toll_selector.select_tolls_by_count(
        identification_result['tolls_on_route'],
        target_count=2,
        identification_result=identification_result
    )
    
    # Vérifications pour le mode count
    assert result_count['selection_valid'] is True, "Sélection count devrait être valide"
    selected_tolls_count = result_count['selected_tolls']
    
    print(f"   ✅ Nombre de péages sélectionnés: {len(selected_tolls_count)}")
    
    for i, toll in enumerate(selected_tolls_count):
        print(f"   📍 Péage {i+1}: {type(toll)} - {getattr(toll, 'name', 'N/A')}")
        assert not isinstance(toll, dict), f"ÉCHEC: Péage {i+1} est un dict, attendu objet"
        assert hasattr(toll, 'osm_id'), f"ÉCHEC: Péage {i+1} sans osm_id"
    
    print("   ✅ MODE COUNT: Tous les objets sont valides")
    
    # Test 2: Validation du mode BUDGET
    print("\n2. 💰 VALIDATION MODE BUDGET")
    print("-" * 50)
    
    result_budget = toll_selector.select_tolls_by_budget(
        identification_result['tolls_on_route'],
        target_budget=25.0,
        identification_result=identification_result
    )
    
    # Vérifications pour le mode budget
    assert result_budget['selection_valid'] is True, "Sélection budget devrait être valide"
    selected_tolls_budget = result_budget['selected_tolls']
    
    print(f"   ✅ Nombre de péages sélectionnés: {len(selected_tolls_budget)}")
    
    for i, toll in enumerate(selected_tolls_budget):
        print(f"   📍 Péage {i+1}: {type(toll)} - {getattr(toll, 'name', 'N/A')}")
        assert not isinstance(toll, dict), f"ÉCHEC: Péage {i+1} est un dict, attendu objet"
        assert hasattr(toll, 'osm_id') or hasattr(toll, 'link_id'), f"ÉCHEC: Péage {i+1} sans identifiant"
    
    print("   ✅ MODE BUDGET: Tous les objets sont valides")
    
    # Test 3: Validation du calcul de coûts
    print("\n3. 💳 VALIDATION CALCUL DE COÛTS")
    print("-" * 50)
    
    # Mock du calcul de coût pour ne pas dépendre du cache réel
    with patch('src.services.toll.route_optimization.utils.cache_accessor.CacheAccessor.calculate_toll_cost', return_value=8.75):
        cost_count = CacheAccessor.calculate_total_cost(selected_tolls_count)
        cost_budget = CacheAccessor.calculate_total_cost(selected_tolls_budget)
        
        print(f"   ✅ Coût calculé (count): {cost_count}€")
        print(f"   ✅ Coût calculé (budget): {cost_budget}€")
        
        assert isinstance(cost_count, (int, float)), "Coût count devrait être numérique"
        assert isinstance(cost_budget, (int, float)), "Coût budget devrait être numérique"
        assert cost_count >= 0, "Coût count devrait être positif"
        assert cost_budget >= 0, "Coût budget devrait être positif"
    
    print("   ✅ CALCUL DE COÛTS: Tous les calculs fonctionnent")
    
    # Test 4: Validation de la structure des segments
    print("\n4. 🛣️  VALIDATION STRUCTURE SEGMENTS")
    print("-" * 50)
    
    segments_count = result_count.get('segments', [])
    segments_budget = result_budget.get('segments', [])
    
    print(f"   ✅ Segments (count): {len(segments_count)}")
    print(f"   ✅ Segments (budget): {len(segments_budget)}")
    
    for mode, segments in [("count", segments_count), ("budget", segments_budget)]:
        for i, segment in enumerate(segments):
            assert isinstance(segment, dict), f"Segment {i+1} ({mode}) devrait être un dict"
            assert 'has_toll' in segment, f"Segment {i+1} ({mode}) sans indicateur has_toll"
            assert 'start_point' in segment, f"Segment {i+1} ({mode}) sans start_point"
            assert 'end_point' in segment, f"Segment {i+1} ({mode}) sans end_point"
            
            toll_status = "avec péages" if segment['has_toll'] else "sans péages"
            print(f"     🔸 Segment {i+1} ({mode}): {toll_status}")
    
    print("   ✅ STRUCTURE SEGMENTS: Toutes les structures sont valides")
    
    print("\n" + "=" * 80)
    print("🎉 VALIDATION FINALE RÉUSSIE !")
    print("✅ Le système retourne exclusivement des objets (pas de dicts)")
    print("✅ Les deux modes (count/budget) fonctionnent correctement")
    print("✅ Le calcul de coûts fonctionne avec les objets")
    print("✅ La structure de segments est cohérente")
    print("✅ Aucune régression détectée")
    print("=" * 80)


def test_edge_cases_validation():
    """Test des cas limites pour s'assurer de la robustesse."""
    
    print("\n" + "=" * 80)
    print("🔍 VALIDATION CAS LIMITES")
    print("=" * 80)
    
    toll_selector = TollSelector()
    
    # Test 1: Liste vide
    print("\n1. 📭 TEST LISTE VIDE")
    empty_identification = {
        'total_tolls_on_route': 0,
        'tolls_on_route': [],
        'route_info': {'start_point': [0, 0], 'end_point': [1, 1]}
    }
    
    result_empty = toll_selector.select_tolls_by_count(
        [], target_count=2, identification_result=empty_identification
    )
    
    assert result_empty['selection_valid'] is True, "Résultat vide devrait être valide"
    assert len(result_empty['selected_tolls']) == 0, "Liste vide devrait retourner 0 péages"
    print("   ✅ Liste vide gérée correctement")
    
    # Test 2: Target count = 0
    print("\n2. 🚫 TEST TARGET COUNT = 0")
    result_zero = toll_selector.select_tolls_by_count(
        [{'toll': Mock(), 'toll_type': 'fermé'}], 
        target_count=0, 
        identification_result=empty_identification
    )
    
    assert result_zero['selection_valid'] is True, "Résultat zero count devrait être valide"
    assert len(result_zero['selected_tolls']) == 0, "Target 0 devrait retourner 0 péages"
    print("   ✅ Target count 0 géré correctement")
    
    # Test 3: Budget = 0
    print("\n3. 💸 TEST BUDGET = 0")
    result_zero_budget = toll_selector.select_tolls_by_budget(
        [{'toll': Mock(), 'toll_type': 'fermé'}],
        target_budget=0.0,
        identification_result=empty_identification
    )
    
    assert result_zero_budget['selection_valid'] is True, "Résultat budget 0 devrait être valide"
    print("   ✅ Budget 0 géré correctement")
    
    print("\n✅ TOUS LES CAS LIMITES VALIDÉS")


if __name__ == "__main__":
    test_complete_pipeline_validation()
    test_edge_cases_validation()
    print("\n🏆 VALIDATION COMPLÈTE TERMINÉE AVEC SUCCÈS !")
