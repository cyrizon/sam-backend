"""
Calculer la distance entre la sortie trouvée et le péage Saint-Maurice.
"""

import math

def calculate_distance(coord1, coord2):
    """Calcule la distance entre deux points (formule haversine)."""
    lat1, lon1 = math.radians(coord1[1]), math.radians(coord1[0])
    lat2, lon2 = math.radians(coord2[1]), math.radians(coord2[0])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return 6371.0 * c  # Rayon de la Terre en km

# Coordonnées données
sortie_coords = [6.766417, 47.4650316]  # [lon, lat] - sortie ref=6.1
peage_coords = [6.6709828, 47.4252307]  # [lon, lat] - péage Saint-Maurice

distance = calculate_distance(sortie_coords, peage_coords)
print(f"Distance entre la sortie (ref=6.1) et le péage Saint-Maurice : {distance:.2f} km")

# Vérifions si c'est cohérent (la sortie devrait être avant le péage)
if distance < 10:  # Distance raisonnable pour une sortie avant péage
    print("✅ Distance cohérente pour une sortie avant péage")
else:
    print("⚠️ Distance importante, vérifier la logique")
