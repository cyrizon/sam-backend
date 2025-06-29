"""
Test Budget Progressive
======================

Test de la logique progressive du budget optimizer.
"""

def test_progressive_replacement():
    """Test de la sélection progressive des entrées."""
    print("🧪 Test de la sélection progressive...")
    
    try:
        from src.services.toll.route_optimization.toll_analysis.budget.budget_optimizer import BudgetOptimizer
        from src.services.toll.route_optimization.utils.cache_accessor import CacheAccessor
        
        print("✅ Imports réussis")
        
        # Initialisation
        optimizer = BudgetOptimizer()
        
        print("✅ Initialisation réussie")
        
        # Test de l'optimiseur
        
        # Simuler des entrées de remplacement
        mock_entries = [
            type('MockEntry', (), {
                'link_id': 'ENTRY_001',
                'has_toll': lambda: True,
                'get_start_point': lambda: [2.3, 48.8],
                'associated_toll': None
            })(),
            type('MockEntry', (), {
                'link_id': 'ENTRY_002', 
                'has_toll': lambda: True,
                'get_start_point': lambda: [2.4, 48.9],
                'associated_toll': None
            })(),
            type('MockEntry', (), {
                'link_id': 'ENTRY_003',
                'has_toll': lambda: True, 
                'get_start_point': lambda: [2.5, 49.0],
                'associated_toll': None
            })()
        ]
        
        print(f"🎯 Test avec {len(mock_entries)} entrées mock")
        
        # Test progression séquentielle
        for i in range(len(mock_entries) + 1):  # +1 pour tester le dépassement
            entry = optimizer._get_next_replacement(mock_entries)
            if entry:
                print(f"   Tentative {i+1}: {entry.link_id} ✅")
            else:
                print(f"   Tentative {i+1}: Aucune entrée restante ❌")
        
        print(f"📊 Index final : {optimizer.replacement_index}")
        
        # Test réinitialisation
        optimizer.replacement_index = 0
        print(f"🔄 Après réinitialisation : {optimizer.replacement_index}")
        
        # Test avec données de péages
        mock_open_tolls = [{'toll_type': 'ouvert', 'name': 'Ouvert1'}]
        mock_closed_tolls = [
            {'toll_type': 'fermé', 'name': 'Fermé1'},
            {'toll_type': 'fermé', 'name': 'Fermé2'}
        ]
        mock_route_coords = [[2.3, 48.8], [2.5, 49.0]]
        budget_limit = 8.0
        
        print(f"\n💰 Test optimisation complète (budget: {budget_limit}€)")
        
        # Note: Ce test échouera car on n'a pas de vraies entrées, 
        # mais on peut voir la logique en action
        try:
            result = optimizer.optimize_for_budget(
                mock_open_tolls, mock_closed_tolls, 
                budget_limit, mock_route_coords
            )
            
            if result:
                print(f"✅ Résultat obtenu: {result.get('selection_reason', 'N/A')}")
            else:
                print("❌ Aucun résultat")
                
        except Exception as e:
            print(f"⚠️ Erreur attendue (données mock): {e}")
        
        print("\n✅ Test progression séquentielle terminé !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_progressive_replacement()
