"""
Script pour examiner les péages ouverts détectés
-----------------------------------------------
"""

import os
import sys

# Ajouter le répertoire src au path pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.cache.v2.managers.v2_cache_manager_with_pricing import V2CacheManagerWithPricing


def main():
    """Examine les péages ouverts détectés."""
    print("🔍 Examen des péages ouverts détectés")
    print("=" * 50)
    
    # Initialiser le gestionnaire
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    manager = V2CacheManagerWithPricing(data_dir)
    
    # Charger toutes les données
    if not manager.load_all():
        print("❌ Échec du chargement des données")
        return
    
    # Afficher les péages ouverts
    open_tolls = [tb for tb in manager.toll_booths if tb.is_open_toll]
    
    print(f"\n🏪 Péages ouverts détectés ({len(open_tolls)}):")
    for i, toll in enumerate(open_tolls):
        print(f"   {i+1}. {toll.display_name}")
        print(f"      ID: {toll.osm_id}")
        print(f"      Nom: {toll.name}")
        print(f"      Type: {toll.type}")
        print(f"      Opérateur: {toll.operator or 'Non spécifié'}")
        print(f"      Coordonnées: {toll.coordinates}")
        print()
    
    # Afficher les noms chargés depuis le CSV
    print(f"📂 Noms de péages ouverts chargés depuis le CSV:")
    for name in manager.open_tolls_manager.open_toll_names:
        print(f"   - '{name}'")


if __name__ == "__main__":
    main()
