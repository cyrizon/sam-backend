"""
Test de calcul de coût avec péages ouverts
------------------------------------------
"""

import os
import sys

# Ajouter le répertoire src au path pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.cache.v2.managers.v2_cache_manager_with_pricing import V2CacheManagerWithPricing


def main():
    """Test calculs de coûts avec différents types de péages."""
    print("💰 Test de calcul de coût avec péages ouverts")
    print("=" * 60)
    
    # Initialiser le gestionnaire
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    manager = V2CacheManagerWithPricing(data_dir)
    
    # Charger toutes les données
    if not manager.load_all():
        print("❌ Échec du chargement des données")
        return
    
    # Récupérer différents types de péages
    open_tolls = [tb for tb in manager.toll_booths if tb.is_open_toll]
    closed_tolls = [tb for tb in manager.toll_booths if tb.is_closed_toll]
    
    if len(open_tolls) >= 1 and len(closed_tolls) >= 1:
        open_toll = open_tolls[0]
        closed_toll = closed_tolls[0]
        
        print(f"\n🔄 Tests de calcul entre différents types de péages:")
        print(f"   Péage ouvert: {open_toll.display_name} ({open_toll.type})")
        print(f"   Péage fermé: {closed_toll.display_name} ({closed_toll.type})")
        
        # Test 1: Ouvert vers Fermé
        print(f"\n1. 🚪➡️🔒 Ouvert vers Fermé:")
        result = manager.calculate_toll_cost(open_toll.osm_id, closed_toll.osm_id, "1")
        if result:
            print(f"   Coût: {result['cost']:.2f}€" if result['cost'] else "Gratuit")
            print(f"   Explication: {result['explanation']}")
        
        # Test 2: Fermé vers Ouvert
        print(f"\n2. 🔒➡️🚪 Fermé vers Ouvert:")
        result = manager.calculate_toll_cost(closed_toll.osm_id, open_toll.osm_id, "1")
        if result:
            print(f"   Coût: {result['cost']:.2f}€" if result['cost'] else "Gratuit")
            print(f"   Explication: {result['explanation']}")
        
        # Test 3: Ouvert vers Ouvert (si on a 2 péages ouverts)
        if len(open_tolls) >= 2:
            open_toll2 = open_tolls[1]
            print(f"\n3. 🚪➡️🚪 Ouvert vers Ouvert:")
            result = manager.calculate_toll_cost(open_toll.osm_id, open_toll2.osm_id, "1")
            if result:
                print(f"   Coût: {result['cost']:.2f}€" if result['cost'] else "Gratuit")
                print(f"   Explication: {result['explanation']}")
        
        # Test 4: Fermé vers Fermé (déjà testé précédemment)
        print(f"\n4. 🔒➡️🔒 Fermé vers Fermé (opérateurs différents):")
        if len(closed_tolls) >= 2:
            closed_toll2 = closed_tolls[1]
            result = manager.calculate_toll_cost(closed_toll.osm_id, closed_toll2.osm_id, "1")
            if result:
                print(f"   Coût: {result['cost']:.2f}€" if result['cost'] else "Gratuit")
                print(f"   Explication: {result['explanation']}")
        
        # Test 5: Opérateurs équivalents (ASF, COFIROUTE, ESCOTA)
        print(f"\n5. 🔒➡️🔒 Fermé vers Fermé (opérateurs équivalents):")
        equivalent_operators = ["ASF", "COFIROUTE", "ESCOTA"]
        
        # Chercher des péages avec des opérateurs équivalents
        equivalent_tolls = {}
        for toll in closed_tolls:
            if toll.operator in equivalent_operators:
                if toll.operator not in equivalent_tolls:
                    equivalent_tolls[toll.operator] = []
                equivalent_tolls[toll.operator].append(toll)
        
        # Test entre deux opérateurs équivalents différents
        if len(equivalent_tolls) >= 2:
            operators = list(equivalent_tolls.keys())
            toll1 = equivalent_tolls[operators[0]][0]
            toll2 = equivalent_tolls[operators[1]][0]
            
            print(f"   Test: {toll1.display_name} ({toll1.operator}) ➡️ {toll2.display_name} ({toll2.operator})")
            result = manager.calculate_toll_cost(toll1.osm_id, toll2.osm_id, "1")
            if result:
                print(f"   Coût: {result['cost']:.2f}€" if result['cost'] else "Gratuit")
                print(f"   Explication: {result['explanation']}")
        else:
            print(f"   ⚠️  Pas assez d'opérateurs équivalents trouvés pour le test")
            print(f"   Opérateurs équivalents disponibles: {list(equivalent_tolls.keys())}")
    
    else:
        print("❌ Pas assez de péages de types différents pour les tests")


if __name__ == "__main__":
    main()
