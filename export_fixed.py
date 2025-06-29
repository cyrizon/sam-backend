"""
Export du nouveau GeoJSON corrigé
"""

from src.cache.v2.managers.v2_cache_manager_with_linking import V2CacheManagerWithLinking
import os

data_dir = 'data'
cache_dir = 'osm_cache_v2_test'

print('📤 Export du nouveau GeoJSON corrigé...')
cache_manager = V2CacheManagerWithLinking(data_dir, cache_dir)
success = cache_manager.load_all_including_motorway_linking()

if success:
    export_path = os.path.join(cache_dir, 'complete_motorway_links_fixed.geojson')
    export_success = cache_manager.export_links_to_geojson(export_path)
    
    if export_success:
        print(f'✅ Export réussi: {export_path}')
        
        # Vérifier quelques coordonnées dans le nouveau fichier
        print('🔍 Vérification du contenu exporté...')
        all_links = cache_manager.get_complete_motorway_links()
        if all_links:
            first_link = all_links[0]
            coords = first_link.get_all_coordinates()
            print(f'   Premier lien: {len(coords)} coordonnées')
            
            # Vérifier les doublons dans les premières coordonnées
            if len(coords) >= 5:
                print('   Premières coordonnées:')
                for i in range(5):
                    print(f'     {i}: {coords[i]}')
    else:
        print('❌ Échec export')
else:
    print('❌ Erreur chargement')
