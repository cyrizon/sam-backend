"""
Test des Index Spatiaux V2
==========================

Test du nouveau système d'index spatial unifié avec cache V2.
"""

from src.services.toll.route_optimization.toll_analysis.spatial.unified_spatial_manager import UnifiedSpatialIndexManager


def test_unified_spatial_indexes():
    """Test complet des index spatiaux unifiés."""
    print("🧪 Test des index spatiaux unifiés...")
    
    # Initialiser le gestionnaire unifié
    unified_manager = UnifiedSpatialIndexManager()
    
    # Statistiques globales
    stats = unified_manager.get_unified_stats()
    print("\n📊 Statistiques des index:")
    for index_name, index_stats in stats.items():
        if isinstance(index_stats, dict):
            print(f"   • {index_name}:")
            for key, value in index_stats.items():
                print(f"     - {key}: {value}")
        else:
            print(f"   • {index_name}: {index_stats}")
    
    # Test recherche de péages
    print(f"\n🎯 Test recherche de péages...")
    route_coords = [[2.3522, 48.8566], [2.4522, 48.9566]]  # Paris approximatif
    nearby_tolls = unified_manager.get_nearby_tolls(route_coords)
    print(f"   Péages trouvés: {len(nearby_tolls)}")
    
    if nearby_tolls:
        first_toll = nearby_tolls[0]
        print(f"   Premier péage: {first_toll.display_name} ({first_toll.operator})")
        print(f"   Type: {'Ouvert' if first_toll.is_open_toll else 'Fermé'}")
    
    # Test recherche d'entrées
    print(f"\n🚪 Test recherche d'entrées...")
    test_point = [2.3522, 48.8566]  # Point de test
    nearby_entries = unified_manager.get_nearby_entries(test_point, buffer_km=1.0)
    entries_with_tolls = unified_manager.get_entries_with_tolls()
    
    print(f"   Entrées proches (1km): {len(nearby_entries)}")
    print(f"   Entrées avec péages (total): {len(entries_with_tolls)}")
    
    # Test recherche d'entrées de remplacement
    if nearby_tolls:
        toll_coords = nearby_tolls[0].get_coordinates()
        replacement_entries = unified_manager.find_replacement_entries_for_toll(
            toll_coords, buffer_km=0.5
        )
        print(f"   Entrées de remplacement: {len(replacement_entries)}")
    
    # Test recherche de sorties
    print(f"\n🚗 Test recherche de sorties...")
    nearby_exits = unified_manager.get_nearby_exits(test_point, buffer_km=1.0)
    exits_with_tolls = unified_manager.get_exits_with_tolls()
    
    print(f"   Sorties proches (1km): {len(nearby_exits)}")
    print(f"   Sorties avec péages (total): {len(exits_with_tolls)}")
    
    print(f"\n✅ Test des index spatiaux terminé !")
    return True


if __name__ == "__main__":
    test_unified_spatial_indexes()
