"""
route_utils.py
-------------

Fonctions utilitaires communes pour les services de routage.
"""
import copy

def is_toll_open_system(toll_id):
    """
    Détermine si un péage est à système ouvert à partir de son ID.
    
    Args:
        toll_id: Identifiant du péage
        
    Returns:
        bool: True si c'est un système ouvert, False sinon
    """
    if not toll_id:
        return False
    toll_id = str(toll_id).strip().lower()
    return "_o" in toll_id  # "_o" pour les systèmes ouverts vs "_f" pour les fermés

def merge_routes(route1, route2):
    """
    Fusionne deux itinéraires GeoJSON en un seul.
    
    Args:
        route1: Premier itinéraire GeoJSON
        route2: Second itinéraire GeoJSON
        
    Returns:
        dict: Itinéraire GeoJSON fusionné
    """
    # Créer une copie du premier itinéraire
    merged = copy.deepcopy(route1)
    
    # Extraire les propriétés des deux itinéraires
    props1 = route1["features"][0]["properties"]
    props2 = route2["features"][0]["properties"]
    
    # Fusionner les géométries
    coords1 = route1["features"][0]["geometry"]["coordinates"]
    coords2 = route2["features"][0]["geometry"]["coordinates"]
    
    # Si le dernier point de route1 est le même que le premier de route2, on l'enlève
    if coords1[-1] == coords2[0]:
        merged["features"][0]["geometry"]["coordinates"] = coords1 + coords2[1:]
    else:
        merged["features"][0]["geometry"]["coordinates"] = coords1 + coords2
    
    # Fusionner les propriétés (distance, durée, etc.)
    merged["features"][0]["properties"]["summary"] = {
        "distance": props1["summary"]["distance"] + props2["summary"]["distance"],
        "duration": props1["summary"]["duration"] + props2["summary"]["duration"]
    }
    
    return merged
