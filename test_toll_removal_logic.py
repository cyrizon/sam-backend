#!/usr/bin/env python3
"""
Test de la logique de suppression des péages
============================================

Test des nouvelles règles de suppression :
1. Toujours essayer de supprimer les péages fermés en premier
2. Ne supprimer les péages ouverts que si pas assez de fermés disponibles  
3. Ne jamais laisser un seul péage fermé isolé (minimum 2 fermés ou 0)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.toll.route_optimization.toll_analysis.toll_selector import TollSelector

def create_test_toll(name: str, toll_type: str, osm_id: int):
    """Crée un péage de test."""
    return {
        'osm_id': osm_id,
        'name': name,
        'toll_type': toll_type,
        'coordinates': [2.0 + osm_id * 0.01, 46.0 + osm_id * 0.01]
    }

def test_scenario_1_only_closed():
    """Test: Que des péages fermés."""
    print("🧪 Test 1: Que des péages fermés")
    
    selector = TollSelector()
    
    # 5 péages fermés, demander 3
    tolls = [
        create_test_toll(f"Fermé {i}", "fermé", i) for i in range(1, 6)
    ]
    
    print("   Configuration: 5 fermés → demander 3")
    result = selector._remove_tolls_to_match_count(tolls, 3)
    
    print(f"   Résultat valide: {result['selection_valid']}")
    print(f"   Péages sélectionnés: {len(result['selected_tolls'])}")
    print(f"   Péages supprimés: {len(result['removed_tolls'])}")
    
    # Doit être valide car 3 fermés restent (> 1)
    assert result['selection_valid'] == True
    assert len(result['selected_tolls']) == 3
    assert len(result['removed_tolls']) == 2
    print("   ✅ Test 1 réussi\n")

def test_scenario_2_would_isolate_closed():
    """Test: Suppression qui isolerait un fermé."""
    print("🧪 Test 2: Suppression qui isolerait un fermé")
    
    selector = TollSelector()
    
    # 3 péages fermés, demander 1 → laisserait 1 fermé isolé
    tolls = [
        create_test_toll(f"Fermé {i}", "fermé", i) for i in range(1, 4)
    ]
    
    print("   Configuration: 3 fermés → demander 1 (laisserait 1 isolé)")
    result = selector._remove_tolls_to_match_count(tolls, 1)
    
    print(f"   Résultat valide: {result['selection_valid']}")
    print(f"   Raison: {result['reason']}")
    
    # Doit être invalide car laisserait 1 fermé isolé
    assert result['selection_valid'] == False
    assert len(result['selected_tolls']) == 0
    print("   ✅ Test 2 réussi\n")

def test_scenario_3_mixed_prefer_closed():
    """Test: Péages mixtes, préférer supprimer les fermés."""
    print("🧪 Test 3: Péages mixtes - préférer fermés")
    
    selector = TollSelector()
    
    # 3 fermés + 2 ouverts, demander 3 → supprimer 2 fermés
    tolls = [
        create_test_toll("Fermé 1", "fermé", 1),
        create_test_toll("Ouvert 1", "ouvert", 2),
        create_test_toll("Fermé 2", "fermé", 3),
        create_test_toll("Fermé 3", "fermé", 4),
        create_test_toll("Ouvert 2", "ouvert", 5)
    ]
    
    print("   Configuration: 3 fermés + 2 ouverts → demander 3")
    result = selector._remove_tolls_to_match_count(tolls, 3)
    
    print(f"   Résultat valide: {result['selection_valid']}")
    print(f"   Péages sélectionnés: {len(result['selected_tolls'])}")
    print(f"   Péages supprimés: {len(result['removed_tolls'])}")
    
    # Compter les types dans la sélection finale
    selected_closed = sum(1 for t in result['selected_tolls'] if selector._extract_toll_type(t) == 'fermé')
    selected_open = sum(1 for t in result['selected_tolls'] if selector._extract_toll_type(t) == 'ouvert')
    
    print(f"   Sélectionnés - Fermés: {selected_closed}, Ouverts: {selected_open}")
    
    # Doit préférer garder les ouverts et supprimer les fermés (mais pas tous)
    assert result['selection_valid'] == True
    assert len(result['selected_tolls']) == 3
    assert selected_closed >= 2  # Au minimum 2 fermés gardés ou 0
    print("   ✅ Test 3 réussi\n")

def test_scenario_4_mixed_avoid_isolation():
    """Test: Péages mixtes, éviter l'isolation."""
    print("🧪 Test 4: Péages mixtes - éviter isolation")
    
    selector = TollSelector()
    
    # 2 fermés + 3 ouverts, demander 2 → ne peut pas supprimer qu'1 fermé
    tolls = [
        create_test_toll("Fermé 1", "fermé", 1),
        create_test_toll("Ouvert 1", "ouvert", 2),
        create_test_toll("Fermé 2", "fermé", 3),
        create_test_toll("Ouvert 2", "ouvert", 4),
        create_test_toll("Ouvert 3", "ouvert", 5)
    ]
    
    print("   Configuration: 2 fermés + 3 ouverts → demander 2")
    result = selector._remove_tolls_to_match_count(tolls, 2)
    
    print(f"   Résultat valide: {result['selection_valid']}")
    print(f"   Péages sélectionnés: {len(result['selected_tolls'])}")
    
    # Compter les types dans la sélection finale
    selected_closed = sum(1 for t in result['selected_tolls'] if selector._extract_toll_type(t) == 'fermé')
    selected_open = sum(1 for t in result['selected_tolls'] if selector._extract_toll_type(t) == 'ouvert')
    
    print(f"   Sélectionnés - Fermés: {selected_closed}, Ouverts: {selected_open}")
    
    # Doit soit garder 0 fermé, soit 2 fermés (jamais 1)
    assert result['selection_valid'] == True
    assert len(result['selected_tolls']) == 2
    assert selected_closed != 1  # Jamais 1 fermé isolé
    print("   ✅ Test 4 réussi\n")

def test_scenario_5_only_open():
    """Test: Que des péages ouverts."""
    print("🧪 Test 5: Que des péages ouverts")
    
    selector = TollSelector()
    
    # 4 péages ouverts, demander 2
    tolls = [
        create_test_toll(f"Ouvert {i}", "ouvert", i) for i in range(1, 5)
    ]
    
    print("   Configuration: 4 ouverts → demander 2")
    result = selector._remove_tolls_to_match_count(tolls, 2)
    
    print(f"   Résultat valide: {result['selection_valid']}")
    print(f"   Péages sélectionnés: {len(result['selected_tolls'])}")
    print(f"   Péages supprimés: {len(result['removed_tolls'])}")
    
    # Doit être valide, pas de contrainte sur les ouverts
    assert result['selection_valid'] == True
    assert len(result['selected_tolls']) == 2
    assert len(result['removed_tolls']) == 2
    
    # Tous doivent être ouverts
    selected_types = [selector._extract_toll_type(t) for t in result['selected_tolls']]
    assert all(t == 'ouvert' for t in selected_types)
    print("   ✅ Test 5 réussi\n")

def run_all_tests():
    """Exécute tous les tests."""
    print("🚀 Tests de la logique de suppression des péages")
    print("=" * 50)
    
    try:
        test_scenario_1_only_closed()
        test_scenario_2_would_isolate_closed()
        test_scenario_3_mixed_prefer_closed()
        test_scenario_4_mixed_avoid_isolation()
        test_scenario_5_only_open()
        
        print("🎉 Tous les tests de logique réussis !")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
