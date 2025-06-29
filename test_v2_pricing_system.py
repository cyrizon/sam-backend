"""
Test du système de pricing V2
------------------------------

Script de test pour démontrer le fonctionnement du système de pricing intégré au cache V2.
"""

import os
import sys

# Ajouter le répertoire src au path pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.cache.v2.managers.v2_cache_manager_with_pricing import V2CacheManagerWithPricing


def main():
    """Test principal du système de pricing V2."""
    print("🧪 Test du système de pricing V2")
    print("=" * 50)
    
    # Initialiser le gestionnaire
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    manager = V2CacheManagerWithPricing(data_dir)
    
    # Charger toutes les données
    if not manager.load_all():
        print("❌ Échec du chargement des données")
        return
    
    # Afficher le résumé
    print("\n📊 Résumé du cache:")
    summary = manager.get_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    # Test de calcul de coût (si des toll booths sont disponibles)
    if len(manager.toll_booths) >= 2:
        print("\n💰 Test de calcul de coût:")
        toll1 = manager.toll_booths[0]
        toll2 = manager.toll_booths[1]
        
        print(f"   De: {toll1.display_name} ({toll1.type})")
        print(f"   Vers: {toll2.display_name} ({toll2.type})")
        
        # Calculer le coût pour différentes classes
        for vehicle_class in ["1", "2", "3"]:
            result = manager.calculate_toll_cost(
                toll1.osm_id, 
                toll2.osm_id, 
                vehicle_class
            )
            
            if result and result.get("cost"):
                print(f"   Classe {vehicle_class}: {result['cost']:.2f}€ ({result['explanation']})")
            else:
                print(f"   Classe {vehicle_class}: {result['explanation'] if result else 'Erreur'}")
    
    # Afficher quelques exemples de toll booths
    print(f"\n🏪 Exemples de toll booths ({min(5, len(manager.toll_booths))} premiers):")
    for i, tb in enumerate(manager.toll_booths[:5]):
        print(f"   {i+1}. {tb.display_name}")
        print(f"      ID: {tb.osm_id}")
        print(f"      Type: {'Ouvert' if tb.is_open_toll else 'Fermé'}")
        print(f"      Opérateur: {tb.operator or 'Non spécifié'}")
        print(f"      Coordonnées: {tb.coordinates}")
        print()


if __name__ == "__main__":
    main()
