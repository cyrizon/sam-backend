"""
Test direct de l'IntelligentOptimizer pour debug
"""

import sys
sys.path.append('.')

from src.services.toll.route_optimization.main.intelligent_optimizer import IntelligentOptimizer

class MockORS:
    """Mock ORS service pour les tests"""
    pass

def test_direct_optimizer():
    """Test direct de l'optimiseur pour debug"""
    
    print("🧪 Test direct IntelligentOptimizer")
    
    # Route de Sélestat à Clermont-Ferrand
    coordinates = [
        [7.448405, 48.261682],  # Sélestat
        [3.11506, 45.784359]    # Destination finale
    ]
    
    # Créer l'optimiseur
    ors_service = MockORS()
    optimizer = IntelligentOptimizer(ors_service)
    
    print(f"   Route: {coordinates[0]} → {coordinates[1]}")
    print(f"   Target: 2 péages")
    
    # Appeler l'optimisation
    try:
        result = optimizer.find_optimized_route(
            coordinates=coordinates,
            target_tolls=2,
            optimization_mode='count'
        )
        
        print(f"\n📊 Résultat direct:")
        if result:
            print(f"   ✅ Route trouvée")
            print(f"   Clés: {list(result.keys())}")
            
            # Analyser les champs clés
            print(f"   found_solution: {result.get('found_solution', 'N/A')}")
            print(f"   strategy_used: {result.get('strategy_used', 'N/A')}")
            print(f"   respects_constraint: {result.get('respects_constraint', 'N/A')}")
            print(f"   toll_count: {result.get('toll_count', 0)}")
            print(f"   target_tolls: {result.get('target_tolls', 0)}")
            
            # Vérifier les péages
            tolls = result.get('tolls', [])
            print(f"   Péages retournés: {len(tolls)}")
            for i, toll in enumerate(tolls[:3]):
                toll_name = toll.get('from_name', 'Inconnu')
                print(f"      {i+1}. {toll_name}")
        else:
            print(f"   ❌ Aucun résultat")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_optimizer()
