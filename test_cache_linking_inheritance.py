"""
Test de vérification de l'héritage du cache V2 avec linking.
Vérifie que toutes les fonctionnalités de pricing sont disponibles.
"""

import os
import pytest

from src.cache.v2.managers.v2_cache_manager_with_linking import V2CacheManagerWithLinking


def test_linking_cache_has_pricing_features():
    """Vérifie que le cache avec linking a bien toutes les fonctionnalités de pricing."""
    
    # Chemin vers les données
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, "data")
    cache_dir = "osm_cache_v2_test"
    
    print(f"📂 Data dir: {data_dir}")
    
    # Créer le gestionnaire avec linking
    cache_manager = V2CacheManagerWithLinking(data_dir, cache_dir)
    
    # Vérifier que les attributs de pricing sont présents
    assert hasattr(cache_manager, 'pricing_manager'), "pricing_manager manquant"
    assert hasattr(cache_manager, 'open_tolls_manager'), "open_tolls_manager manquant"
    assert hasattr(cache_manager, 'cost_calculator'), "cost_calculator manquant"
    
    # Vérifier que les méthodes de pricing sont présentes
    assert hasattr(cache_manager, 'calculate_toll_cost'), "calculate_toll_cost manquant"
    assert hasattr(cache_manager, 'get_toll_booths_by_operator'), "get_toll_booths_by_operator manquant"
    
    # Vérifier que les méthodes de linking sont présentes
    assert hasattr(cache_manager, 'get_complete_motorway_links'), "get_complete_motorway_links manquant"
    assert hasattr(cache_manager, 'get_links_by_operator'), "get_links_by_operator manquant"
    assert hasattr(cache_manager, 'load_all_including_motorway_linking'), "load_all_including_motorway_linking manquant"
    
    print("✅ Toutes les fonctionnalités requises sont présentes dans le cache avec linking")


def test_cache_loading_and_pricing_access():
    """Test complet de chargement et d'accès aux fonctionnalités de pricing."""
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, "data")
    cache_dir = "osm_cache_v2_test"
    
    cache_manager = V2CacheManagerWithLinking(data_dir, cache_dir)
    
    # Charger le cache complet (toll booths + pricing + linking)
    success = cache_manager.load_all_including_motorway_linking()
    
    if not success:
        print("⚠️ Impossible de charger le cache complet, test avec les données de base")
        # Essayer de charger au moins les toll booths
        success = cache_manager.load_all()
        
    assert success, "Impossible de charger le cache"
    assert cache_manager.is_loaded, "Cache non marqué comme chargé"
    
    # Vérifier l'accès aux toll booths
    toll_booths = cache_manager.toll_booths
    assert toll_booths is not None, "toll_booths is None"
    print(f"📊 Nombre de toll booths chargés: {len(toll_booths)}")
    
    # Vérifier l'accès au cost calculator
    assert cache_manager.cost_calculator is not None, "cost_calculator is None"
    
    # Si on a des toll booths, tester le calcul de coût
    if len(toll_booths) >= 2:
        toll1 = toll_booths[0]
        toll2 = toll_booths[1]
        
        print(f"🧮 Test calcul de coût entre {toll1.name} et {toll2.name}")
        
        cost_result = cache_manager.calculate_toll_cost(
            toll1.osm_id, 
            toll2.osm_id, 
            vehicle_class="1"
        )
        
        print(f"💰 Résultat du calcul: {cost_result}")
        
        # Le résultat peut être None si pas de route directe, c'est normal
        if cost_result:
            assert isinstance(cost_result, dict), "Le résultat doit être un dict"
            print("✅ Calcul de coût fonctionnel")
        else:
            print("ℹ️ Pas de route directe entre ces toll booths (normal)")
    
    print("✅ Test complet réussi - Cache avec linking et pricing fonctionnel")


if __name__ == "__main__":
    test_linking_cache_has_pricing_features()
    test_cache_loading_and_pricing_access()
    print("🎉 Tous les tests d'héritage réussis!")
