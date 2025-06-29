"""
Test pour calculer la longueur des liens motorway
"""

import math

def calculate_link_length(coordinates):
    """Calcule la longueur d'un lien en mètres"""
    if len(coordinates) < 2:
        return 0
    
    total_distance = 0
    for i in range(1, len(coordinates)):
        lat1, lon1 = coordinates[i-1][1], coordinates[i-1][0]
        lat2, lon2 = coordinates[i][1], coordinates[i][0]
        
        # Distance haversine approximative
        R = 6371000  # Rayon de la Terre en mètres
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        total_distance += distance
    
    return total_distance

# Test avec l'aire problématique
aire_coords = [
    [4.5068569, 45.8717074],
    [4.506783, 45.8716323],
    [4.5066959, 45.871561],
    [4.5064967, 45.8714539],
    [4.5062796, 45.8712707]
]

aire_length = calculate_link_length(aire_coords)
print(f"Longueur de l'aire problématique: {aire_length:.1f} mètres")

# Test avec quelques coordonnées d'une vraie entrée (exemple)
vraie_entree_coords = [
    [4.5000000, 45.8700000],
    [4.5010000, 45.8710000],
    [4.5020000, 45.8720000],
    [4.5030000, 45.8730000],
    [4.5040000, 45.8740000],
    [4.5050000, 45.8750000],
    [4.5060000, 45.8760000],
    [4.5070000, 45.8770000]
]

vraie_entree_length = calculate_link_length(vraie_entree_coords)
print(f"Longueur d'une vraie entrée (estimée): {vraie_entree_length:.1f} mètres")

print(f"\nSeuil suggéré: {max(200, aire_length * 2):.0f} mètres")
