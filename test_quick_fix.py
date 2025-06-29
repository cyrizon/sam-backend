"""
Test rapide de vérification de la correction des doublons
"""

print('🧪 Test de la correction appliquée')

try:
    from src.cache.v2.managers.v2_cache_manager_with_linking import V2CacheManagerWithLinking
    import os

    data_dir = 'data'
    cache_dir = 'osm_cache_v2_test'

    cache_manager = V2CacheManagerWithLinking(data_dir, cache_dir)
    success = cache_manager.load_all_including_motorway_linking()

    if success:
        all_links = cache_manager.get_complete_motorway_links()
        print(f'📊 {len(all_links)} liens chargés')
        
        if all_links:
            # Tester les 5 premiers liens
            total_doublons = 0
            for i in range(min(5, len(all_links))):
                link = all_links[i]
                coords = link.get_all_coordinates()
                
                doublons = 0
                for j in range(len(coords) - 1):
                    if coords[j] == coords[j + 1]:
                        doublons += 1
                
                total_doublons += doublons
                print(f'   Lien {i+1}: {len(coords)} coords, {doublons} doublons')
            
            if total_doublons == 0:
                print('✅ Correction appliquée avec succès!')
            else:
                print(f'⚠️ {total_doublons} doublons trouvés')
        else:
            print('⚠️ Aucun lien trouvé')
    else:
        print('❌ Erreur de chargement')

except Exception as e:
    print(f'❌ Erreur: {e}')
