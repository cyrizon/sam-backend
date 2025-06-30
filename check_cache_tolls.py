"""
Test pour vérifier les péages disponibles dans le cache et fixer le test
"""

from src.services.toll.route_optimization.utils.cache_accessor import CacheAccessor


def check_available_tolls():
    """Vérifie quels péages sont disponibles dans le cache."""
    
    print("Vérification des péages disponibles dans le cache...")
    
    try:
        toll_stations = CacheAccessor.get_toll_stations()
        print(f"Total de péages dans le cache: {len(toll_stations)}")
        
        # Afficher quelques péages pour test
        print("\nPremiers péages disponibles:")
        for i, toll in enumerate(toll_stations[:10]):
            print(f"  {i+1}. OSM ID: {toll.osm_id}, Nom: {toll.name}, Opérateur: {getattr(toll, 'operator', 'N/A')}")
        
        # Chercher spécifiquement des péages APRR fermés
        aprr_tolls = []
        for toll in toll_stations:
            if hasattr(toll, 'operator') and 'APRR' in str(toll.operator):
                aprr_tolls.append(toll)
            
        print(f"\nPéages APRR trouvés: {len(aprr_tolls)}")
        for i, toll in enumerate(aprr_tolls[:5]):
            print(f"  {i+1}. OSM ID: {toll.osm_id}, Nom: {toll.name}")
            
        return toll_stations
        
    except Exception as e:
        print(f"Erreur: {e}")
        return []


if __name__ == "__main__":
    check_available_tolls()
