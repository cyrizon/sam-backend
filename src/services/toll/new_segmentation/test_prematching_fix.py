"""
test_prematching_fix.py
----------------------

Test rapide pour vérifier la correction du pré-matching avec les noms CSV.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.osm_data_cache import osm_data_cache


def test_prematching_names():
    """Test rapide du pré-matching avec affichage des noms CSV."""
    print("🧪 Test correction pré-matching - Noms CSV")
    
    # Initialiser le cache OSM (cela déclenchera le pré-matching)
    print("📁 Initialisation cache OSM...")
    osm_data_cache.initialize()
    
    # Vérifier le parser
    osm_parser = osm_data_cache._osm_parser
    if not osm_parser or not hasattr(osm_parser, 'toll_stations'):
        print("❌ Parser OSM non disponible")
        return
    
    # Examiner quelques péages matchés
    print(f"\n📊 {len(osm_parser.toll_stations)} stations de péage chargées")
    print("🔍 Échantillon de péages pré-matchés :")
    
    matched_count = 0
    for i, toll_station in enumerate(osm_parser.toll_stations[:20]):  # Examiner les 20 premiers
        if hasattr(toll_station, 'csv_match') and toll_station.csv_match:
            matched_count += 1
            csv_name = toll_station.csv_match.get('name', 'Nom CSV manquant')
            csv_role = toll_station.csv_match.get('role', 'Role inconnu')
            csv_id = toll_station.csv_match.get('id', 'ID manquant')
            
            print(f"   ✅ {toll_station.name or 'Sans nom'}")
            print(f"      → CSV: {csv_name} ({csv_id}) [{csv_role}]")
            
            if matched_count >= 10:  # Afficher max 10 péages matchés
                break
    
    if matched_count == 0:
        print("   ⚠️ Aucun péage matché trouvé dans l'échantillon")
        
        # Afficher quelques péages non-matchés pour debug
        print("\n🔍 Échantillon de péages non-matchés :")
        for i, toll_station in enumerate(osm_parser.toll_stations[:5]):
            if not hasattr(toll_station, 'csv_match') or not toll_station.csv_match:
                print(f"   🔍 {toll_station.name or 'Sans nom'} → Non matché")
    
    print(f"\n✅ Test terminé : {matched_count} péages matchés dans l'échantillon")


if __name__ == "__main__":
    test_prematching_names()
