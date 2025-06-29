"""
Debug spécifique de l'optimisation des éléments.
"""

import sys
sys.path.append('.')

from src.services.toll.route_optimization.main.intelligent_optimizer import IntelligentOptimizer
from src.services.toll.route_optimization.utils.cache_accessor import CacheAccessor

def debug_optimization():
    """Test simple d'optimisation d'éléments."""
    
    # Route de Sélestat à Dijon
    start_coords = [7.448595, 48.262004]
    end_coords = [5.037793, 47.317743]
    
    # Initialiser le système
    # optimizer = IntelligentOptimizer(mock_ors)  # Pas besoin pour ce test
    
    # Données de test simulées pour un péage - UTILISER DE VRAIES COORDONNÉES
    toll_data = {
        'name': 'Fontaine Larivière',
        'coordinates': [6.9816474, 47.6761296],  # Vraies coordonnées du cache
        'toll_type': 'ouvert',
        'osm_id': 'node/215113122'  # Vrai OSM ID du cache
    }
    
    print("🔍 Debug de l'optimisation d'éléments")
    print(f"   Péage test : {toll_data['name']} (vraies coordonnées)")
    print(f"   Type : {toll_data['toll_type']}")
    print(f"   Coordonnées : {toll_data['coordinates']}")
    print(f"   OSM ID : {toll_data['osm_id']}")
    
    # Test de l'analyseur
    from src.services.toll.route_optimization.toll_analysis.selection_analyzer import SelectionAnalyzer
    analyzer = SelectionAnalyzer()
    
    # Test avec données complètes
    selection_result = {
        'selection_valid': True,
        'selected_tolls': [toll_data]
    }
    
    print("\n🔧 Test optimisation...")
    result = analyzer.analyze_selection_for_optimization(
        selection_result, 
        [start_coords, end_coords]
    )
    
    print(f"\n📋 Résultat :")
    print(f"   Optimisation appliquée : {result.get('optimization_applied', False)}")
    print(f"   Éléments optimisés : {result.get('elements_optimized', 0)}")
    print(f"   Péages sélectionnés : {len(result.get('selected_tolls', []))}")
    
    # Vérifier les éléments optimisés
    for i, toll in enumerate(result.get('selected_tolls', [])):
        print(f"   Élément {i+1} : {type(toll).__name__}")
        if hasattr(toll, 'display_name'):
            print(f"      Nom : {toll.display_name}")
        elif hasattr(toll, 'name'):
            print(f"      Nom : {toll.name}")
    
    # Debug additionnel : vérifier le cache
    print(f"\n🔍 Debug cache :")
    toll_stations = CacheAccessor.get_toll_stations()
    print(f"   Nombre de TollBoothStations : {len(toll_stations)}")
    
    # Chercher des péages dans la région Sélestat-Dijon
    test_coords = [6.8380607, 47.7030708]
    region_coords = [6.5, 47.5]  # Région approximative
    print(f"   Recherche dans la région de l'Alsace/Bourgogne :")
    
    found_stations = []
    for station in toll_stations:
        coords = station.get_coordinates()
        if coords and len(coords) >= 2:
            # Vérifier si c'est dans la région (longitude 5-8, latitude 46-49)
            if 5.0 <= coords[0] <= 8.0 and 46.0 <= coords[1] <= 49.0:
                dx = coords[0] - test_coords[0]
                dy = coords[1] - test_coords[1]
                distance = ((dx * dx + dy * dy) ** 0.5) * 111
                found_stations.append((station, distance))
    
    # Trier par distance
    found_stations.sort(key=lambda x: x[1])
    
    print(f"   Péages trouvés dans la région (top 10) :")
    for i, (station, distance) in enumerate(found_stations[:10]):
        coords = station.get_coordinates()
        print(f"     {i+1}. {station.display_name}")
        print(f"        Coords: {coords}")
        print(f"        Distance: {distance:.2f}km")
        print(f"        OSM_ID: {station.osm_id}")
        
        # Tester avec ces coordonnées
        if i == 0:  # Tester avec le plus proche
            print(f"\n   🧪 Test avec le péage le plus proche : {station.display_name}")
            test_toll_data = {
                'name': station.display_name,
                'coordinates': coords,
                'toll_type': 'ouvert',
                'osm_id': station.osm_id
            }
            
            # Test simple
            from src.services.toll.route_optimization.toll_analysis.selection_analyzer import SelectionAnalyzer
            analyzer = SelectionAnalyzer()
            result_station = analyzer._get_toll_booth_station(test_toll_data)
            print(f"       Résultat : {'✅ Trouvé' if result_station else '❌ Non trouvé'}")
            if result_station:
                print(f"       Nom trouvé : {result_station.display_name}")
        
        if i >= 4:  # Limiter l'affichage
            break

if __name__ == "__main__":
    debug_optimization()
