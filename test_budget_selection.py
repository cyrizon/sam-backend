"""
Test Budget Selection
====================

Test du nouveau système de sélection par budget avec cache V2.
"""

def test_budget_selection():
    """Test de la sélection par budget."""
    print("🧪 Test de la sélection par budget...")
    
    try:
        # Import du nouveau système
        from src.services.toll.route_optimization.toll_analysis.budget.budget_selector import BudgetTollSelector
        from src.services.toll.route_optimization.toll_analysis.toll_selector import TollSelector
        
        print("✅ Imports réussis")
        
        # Test d'initialisation
        budget_selector = BudgetTollSelector()
        toll_selector = TollSelector()
        
        print("✅ Initialisation réussie")
        
        # Test avec des données simulées
        mock_tolls = [
            {
                'toll_type': 'ouvert',
                'name': 'Péage Ouvert',
                'coordinates': [2.3, 48.8],
                'associated_toll': None
            },
            {
                'toll_type': 'fermé',
                'name': 'Péage Fermé 1',
                'coordinates': [2.4, 48.9],
                'associated_toll': None
            },
            {
                'toll_type': 'fermé',
                'name': 'Péage Fermé 2',
                'coordinates': [2.5, 49.0],
                'associated_toll': None
            }
        ]
        
        mock_route_coords = [[2.3, 48.8], [2.5, 49.0]]
        budget_limit = 10.0  # 10€ max
        
        print(f"📊 Test avec {len(mock_tolls)} péages, budget: {budget_limit}€")
        
        # Test sélection par budget
        result = budget_selector.select_tolls_by_budget(
            mock_tolls, budget_limit, mock_route_coords
        )
        
        if result:
            print(f"✅ Sélection réussie:")
            print(f"   • Péages sélectionnés: {len(result.get('selected_tolls', []))}")
            print(f"   • Coût total: {result.get('total_cost', 0)}€")
            print(f"   • Raison: {result.get('selection_reason', 'N/A')}")
        else:
            print("❌ Échec de la sélection")
        
        # Test via TollSelector principal
        identification_result = {
            'route_coordinates': mock_route_coords,
            'total_tolls_on_route': len(mock_tolls)
        }
        
        result2 = toll_selector.select_tolls_by_budget(
            mock_tolls, budget_limit, identification_result
        )
        
        if result2:
            print("✅ Test via TollSelector principal réussi")
        else:
            print("❌ Échec via TollSelector principal")
        
        print("\n✅ Test de sélection par budget terminé !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_budget_selection()
