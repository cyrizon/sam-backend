"""
Test des opérateurs équivalents
------------------------------

Test spécifique pour vérifier que ASF, COFIROUTE et ESCOTA sont bien considérés comme équivalents.
"""

import os
import sys

# Ajouter le répertoire src au path pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.cache.v2.managers.v2_cache_manager_with_pricing import V2CacheManagerWithPricing


def main():
    """Test des opérateurs équivalents."""
    print("🔗 Test des opérateurs équivalents")
    print("=" * 50)
    
    # Initialiser le gestionnaire
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    manager = V2CacheManagerWithPricing(data_dir)
    
    # Charger toutes les données
    if not manager.load_all():
        print("❌ Échec du chargement des données")
        return
    
    # Opérateurs équivalents à tester
    equivalent_operators = ["ASF", "COFIROUTE", "ESCOTA"]
    
    print(f"\n🔗 Opérateurs équivalents: {', '.join(equivalent_operators)}")
    
    # Grouper les péages par opérateur équivalent
    equivalent_tolls = {}
    for toll in manager.toll_booths:
        if toll.is_closed_toll and toll.operator in equivalent_operators:
            if toll.operator not in equivalent_tolls:
                equivalent_tolls[toll.operator] = []
            equivalent_tolls[toll.operator].append(toll)
    
    print(f"\n📊 Péages trouvés par opérateur équivalent:")
    for operator, tolls in equivalent_tolls.items():
        print(f"   {operator}: {len(tolls)} péages")
        # Afficher quelques exemples
        for i, toll in enumerate(tolls[:3]):
            print(f"      - {toll.display_name}")
        if len(tolls) > 3:
            print(f"      ... et {len(tolls) - 3} autres")
    
    # Tests de compatibilité entre opérateurs équivalents
    print(f"\n💰 Tests de calcul de coût entre opérateurs équivalents:")
    
    test_combinations = [
        ("ASF", "COFIROUTE"),
        ("ASF", "ESCOTA"),
        ("COFIROUTE", "ESCOTA")
    ]
    
    for op1, op2 in test_combinations:
        if op1 in equivalent_tolls and op2 in equivalent_tolls:
            toll1 = equivalent_tolls[op1][0]
            toll2 = equivalent_tolls[op2][0]
            
            print(f"\n🔗 {op1} ➡️ {op2}:")
            print(f"   De: {toll1.display_name} ({toll1.operator})")
            print(f"   Vers: {toll2.display_name} ({toll2.operator})")
            
            result = manager.calculate_toll_cost(toll1.osm_id, toll2.osm_id, "1")
            if result:
                cost = result.get('cost', 0)
                if cost and cost > 0:
                    print(f"   ✅ Coût: {cost:.2f}€ - Opérateurs compatibles!")
                else:
                    print(f"   ❌ Coût: 0€ - Opérateurs non compatibles")
                print(f"   Explication: {result['explanation']}")
            else:
                print(f"   ❌ Erreur de calcul")
        else:
            missing_ops = [op for op in [op1, op2] if op not in equivalent_tolls]
            print(f"\n⚠️  {op1} ➡️ {op2}: Opérateur(s) manquant(s): {missing_ops}")
    
    # Test avec un opérateur non équivalent
    print(f"\n🚫 Test avec un opérateur NON équivalent:")
    non_equivalent_operators = ["APRR", "AREA", "SANEF"]
    
    for non_eq_op in non_equivalent_operators:
        non_eq_tolls = [t for t in manager.toll_booths if t.is_closed_toll and t.operator == non_eq_op]
        if non_eq_tolls and "ASF" in equivalent_tolls:
            toll_asf = equivalent_tolls["ASF"][0]
            toll_non_eq = non_eq_tolls[0]
            
            print(f"\n🚫 ASF ➡️ {non_eq_op} (non équivalent):")
            print(f"   De: {toll_asf.display_name} (ASF)")
            print(f"   Vers: {toll_non_eq.display_name} ({non_eq_op})")
            
            result = manager.calculate_toll_cost(toll_asf.osm_id, toll_non_eq.osm_id, "1")
            if result:
                cost = result.get('cost', 0)
                if cost == 0:
                    print(f"   ✅ Coût: 0€ - Opérateurs incompatibles (attendu)")
                else:
                    print(f"   ❌ Coût: {cost:.2f}€ - Devrait être 0€!")
                print(f"   Explication: {result['explanation']}")
            break


if __name__ == "__main__":
    main()
