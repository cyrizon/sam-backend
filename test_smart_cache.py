"""
test_smart_cache.py
------------------

Script de test pour vérifier le cache intelligent des péages.
"""

from src.services.toll.smart_toll_cache import (
    add_marginal_cost_smart_cached, 
    get_smart_cache_stats, 
    clear_smart_toll_cache,
    log_smart_cache_stats
)

def test_cache_with_sample_tolls():
    """Test le cache avec des péages d'exemple."""
    
    print("=== Test du Cache Intelligent des Péages ===")
    
    # Vider le cache pour commencer proprement
    clear_smart_toll_cache()
    
    # Première séquence de test (similaire à votre cas réel)
    tolls_sequence_1 = [
        {'id': 'APRR_O043'},
        {'id': 'APRR_F085'},
        {'id': 'APRR_F024'},
        {'id': 'APRR_F030'}
    ]
    
    print("\n--- Premier calcul (miss attendu) ---")
    print(f"Avant calcul: {tolls_sequence_1}")
    add_marginal_cost_smart_cached(tolls_sequence_1, "c1")
    print(f"Après calcul: {tolls_sequence_1}")
    
    print("\n--- Statistiques après premier calcul ---")
    log_smart_cache_stats()
    
    # Deuxième appel avec la même séquence (hit attendu)
    tolls_sequence_2 = [
        {'id': 'APRR_O043'},
        {'id': 'APRR_F085'},
        {'id': 'APRR_F024'},
        {'id': 'APRR_F030'}
    ]
    
    print("\n--- Deuxième calcul (hit attendu) ---")
    print(f"Avant calcul: {tolls_sequence_2}")
    add_marginal_cost_smart_cached(tolls_sequence_2, "c1")
    print(f"Après calcul: {tolls_sequence_2}")
    
    print("\n--- Statistiques finales ---")
    log_smart_cache_stats()
    
    # Vérifier que les coûts sont identiques
    total_1 = sum(t.get("cost", 0) for t in tolls_sequence_1)
    total_2 = sum(t.get("cost", 0) for t in tolls_sequence_2)
    
    print(f"\n--- Vérification cohérence ---")
    print(f"Coût séquence 1: {total_1:.2f}€")
    print(f"Coût séquence 2: {total_2:.2f}€")
    print(f"Cohérence: {'✅ OK' if total_1 == total_2 else '❌ ERREUR'}")

if __name__ == "__main__":
    test_cache_with_sample_tolls()
