# 🛠️ Cache Utils - Utilitaires du Cache

## 📋 Vue d'ensemble

Les utilitaires du cache SAM fournissent des fonctions de support partagées pour les calculs géographiques, les transformations de données et les opérations communes utilisées dans tout le système de cache.

## 🏗️ Architecture

```
utils/
├── geographic_utils.py    # Utilitaires géographiques et spatiaux
└── __init__.py
```

## 🎯 Objectifs des utilitaires

### **Réutilisabilité**
- 🔧 **Fonctions communes** : Éviter la duplication de code
- 📐 **Calculs géographiques** : Operations spatiales standardisées
- 🔄 **Transformations** : Conversions de formats et coordonnées
- ✅ **Validation** : Contrôles de données uniformes

### **Performance**
- ⚡ **Optimisations** : Implémentations efficaces des algorithmes courants
- 🧠 **Cache local** : Mise en cache des calculs coûteux
- 📊 **Vectorisation** : Traitement en lot quand possible
- 🔍 **Index intelligents** : Structures de données optimisées

## 🧩 Composants détaillés

### **1. GeographicUtils** - Utilitaires Géographiques

Module principal d'utilitaires pour les calculs géographiques et spatiaux.

#### **Calculs de distance**
```python
from src.cache.utils.geographic_utils import GeographicUtils

# Distance géodésique précise
distance_m = GeographicUtils.calculate_geodesic_distance(
    coord1=[4.8345, 46.7123],  # [longitude, latitude]
    coord2=[4.8234, 46.2891]
)
print(f"Distance: {distance_m:.2f} mètres")

# Distance haversine (plus rapide, légèrement moins précise)
distance_m = GeographicUtils.calculate_haversine_distance(
    coord1=[4.8345, 46.7123],
    coord2=[4.8234, 46.2891]
)

# Distance euclidienne (approximation pour courtes distances)
distance_m = GeographicUtils.calculate_euclidean_distance(
    coord1=[4.8345, 46.7123],
    coord2=[4.8234, 46.2891]
)
```

#### **Calculs géométriques**
```python
# Distance point-à-ligne
point = [4.8300, 46.5000]
line_start = [4.8345, 46.7123]
line_end = [4.8234, 46.2891]

distance_to_line = GeographicUtils.point_to_line_distance(
    point=point,
    line_start=line_start,
    line_end=line_end
)

# Point le plus proche sur une ligne
closest_point = GeographicUtils.closest_point_on_line(
    point=point,
    line_start=line_start,
    line_end=line_end
)

# Vérification si un point est dans un polygone
polygon = [[4.8, 46.5], [4.9, 46.5], [4.9, 46.6], [4.8, 46.6]]
is_inside = GeographicUtils.point_in_polygon(point, polygon)
```

#### **Calculs d'orientation et d'angle**
```python
# Calcul du bearing (azimut) entre deux points
bearing = GeographicUtils.calculate_bearing(
    coord1=[4.8345, 46.7123],
    coord2=[4.8234, 46.2891]
)
print(f"Bearing: {bearing:.1f}°")

# Différence angulaire
angle_diff = GeographicUtils.angle_difference(45.0, 135.0)
print(f"Différence d'angle: {angle_diff:.1f}°")

# Normalisation d'angle
normalized = GeographicUtils.normalize_angle(380.0)  # Retourne 20.0
```

#### **Calculs de bbox et zones**
```python
# Calcul de bounding box pour une liste de points
coordinates = [
    [4.8345, 46.7123],
    [4.8234, 46.2891],
    [4.8567, 46.5432]
]
bbox = GeographicUtils.calculate_bounding_box(coordinates)
print(f"BBox: {bbox}")  # [min_lon, min_lat, max_lon, max_lat]

# Expansion d'une bounding box
expanded_bbox = GeographicUtils.expand_bbox(bbox, buffer_m=1000)

# Centre d'une bounding box
center = GeographicUtils.bbox_center(bbox)
```

#### **Transformations de coordonnées**
```python
# Conversion degrés décimaux vers degrés-minutes-secondes
dms = GeographicUtils.decimal_to_dms(46.7123)
print(f"DMS: {dms}")  # {'degrees': 46, 'minutes': 42, 'seconds': 44.28}

# Conversion inverse
decimal = GeographicUtils.dms_to_decimal(46, 42, 44.28)

# Projection locale (approximation plane)
local_coords = GeographicUtils.to_local_projection(
    coordinates=coordinates,
    reference_point=center
)

# Conversion vers Web Mercator (EPSG:3857)
mercator_coords = GeographicUtils.to_web_mercator(coordinates)
```

#### **Utilitaires pour géométries complexes**
```python
# Simplification de polyline (algorithme Douglas-Peucker)
simplified_line = GeographicUtils.simplify_polyline(
    coordinates=route_coordinates,
    tolerance_m=10.0  # Tolérance en mètres
)

# Calcul de la longueur d'une polyline
total_length_m = GeographicUtils.calculate_polyline_length(route_coordinates)

# Interpolation le long d'une polyline
interpolated_point = GeographicUtils.interpolate_on_polyline(
    coordinates=route_coordinates,
    distance_ratio=0.5  # Point à 50% de la longueur
)

# Échantillonnage équidistant d'une polyline
sampled_points = GeographicUtils.sample_polyline(
    coordinates=route_coordinates,
    sample_distance_m=100.0  # Un point tous les 100 mètres
)
```

#### **Validation géographique**
```python
# Validation de coordonnées
is_valid = GeographicUtils.validate_coordinates([4.8345, 46.7123])

# Validation de longitude
is_valid_lon = GeographicUtils.is_valid_longitude(4.8345)

# Validation de latitude
is_valid_lat = GeographicUtils.is_valid_latitude(46.7123)

# Validation d'une bounding box
is_valid_bbox = GeographicUtils.validate_bbox([-180, -90, 180, 90])

# Détection de coordonnées aberrantes
outliers = GeographicUtils.detect_coordinate_outliers(
    coordinates=coordinates,
    threshold_std=2.0  # 2 écarts-types
)
```

#### **Utilitaires de clustering spatial**
```python
# Clustering DBSCAN pour points géographiques
clusters = GeographicUtils.spatial_clustering(
    coordinates=toll_coordinates,
    eps_m=500.0,        # Distance max entre points du même cluster (mètres)
    min_samples=2       # Nombre min de points par cluster
)

# K-means spatial
centroids = GeographicUtils.kmeans_clustering(
    coordinates=coordinates,
    n_clusters=5
)

# Clustering hiérarchique
hierarchy = GeographicUtils.hierarchical_clustering(
    coordinates=coordinates,
    distance_threshold_m=1000.0
)
```

#### **Optimisations de performance**
```python
class GeographicUtils:
    # Cache pour les calculs coûteux
    _distance_cache = {}
    _bearing_cache = {}
    
    @classmethod
    def calculate_geodesic_distance_cached(cls, coord1, coord2):
        """Distance géodésique avec cache."""
        cache_key = (tuple(coord1), tuple(coord2))
        
        if cache_key in cls._distance_cache:
            return cls._distance_cache[cache_key]
        
        distance = cls.calculate_geodesic_distance(coord1, coord2)
        cls._distance_cache[cache_key] = distance
        
        return distance
    
    @classmethod
    def batch_distance_calculation(cls, coord_pairs):
        """Calcul de distances en lot pour performance."""
        distances = []
        
        # Utilisation de numpy pour vectorisation si disponible
        try:
            import numpy as np
            # Implémentation vectorisée
            distances = cls._vectorized_distance_calculation(coord_pairs)
        except ImportError:
            # Fallback sur boucle classique
            for coord1, coord2 in coord_pairs:
                distances.append(cls.calculate_geodesic_distance(coord1, coord2))
        
        return distances
```

#### **Intégration avec Shapely et rtree**
```python
# Conversion vers objets Shapely
def to_shapely_point(coordinates):
    """Convertit des coordonnées vers un Point Shapely."""
    from shapely.geometry import Point
    return Point(coordinates[0], coordinates[1])

def to_shapely_linestring(coordinates):
    """Convertit une liste de coordonnées vers une LineString Shapely."""
    from shapely.geometry import LineString
    return LineString(coordinates)

# Création d'index spatial rtree
def create_spatial_index(coordinates_list):
    """Crée un index spatial rtree."""
    import rtree.index
    
    idx = rtree.index.Index()
    for i, coords in enumerate(coordinates_list):
        # BBox: (min_lon, min_lat, max_lon, max_lat)
        bbox = (coords[0], coords[1], coords[0], coords[1])
        idx.insert(i, bbox)
    
    return idx

# Requêtes spatiales optimisées
def find_nearby_points(target_coord, coordinates_list, radius_m):
    """Trouve les points proches avec index spatial."""
    
    # Conversion rayon en degrés approximatif
    radius_deg = radius_m / 111320.0  # Approximation à l'équateur
    
    # BBox de recherche
    search_bbox = (
        target_coord[0] - radius_deg,
        target_coord[1] - radius_deg,
        target_coord[0] + radius_deg,
        target_coord[1] + radius_deg
    )
    
    # Index spatial
    spatial_idx = create_spatial_index(coordinates_list)
    
    # Recherche préliminaire avec index
    candidate_indices = list(spatial_idx.intersection(search_bbox))
    
    # Filtrage par distance exacte
    nearby_points = []
    for idx in candidate_indices:
        distance = GeographicUtils.calculate_geodesic_distance(
            target_coord, coordinates_list[idx]
        )
        if distance <= radius_m:
            nearby_points.append({
                'index': idx,
                'coordinates': coordinates_list[idx],
                'distance_m': distance
            })
    
    return sorted(nearby_points, key=lambda x: x['distance_m'])
```

## 🔧 Configuration et utilisation

### **Configuration des utilitaires**
```python
# Configuration globale des utilitaires géographiques
GEOGRAPHIC_CONFIG = {
    "default_precision": 6,           # Précision des coordonnées (décimales)
    "distance_calculation_method": "geodesic",  # geodesic, haversine, euclidean
    "enable_caching": True,           # Cache des calculs
    "cache_size": 1000,              # Taille du cache
    "coordinate_system": "WGS84",     # Système de coordonnées
    "distance_unit": "meters",        # Unité de distance
    "angle_unit": "degrees"           # Unité d'angle
}

# Application de la configuration
GeographicUtils.configure(**GEOGRAPHIC_CONFIG)
```

### **Utilisation dans le contexte du cache**
```python
# Intégration avec les composants du cache
def enhance_toll_booths_with_geographic_info(toll_booths):
    """Enrichit les péages avec des informations géographiques."""
    
    # Calcul du centre géographique
    all_coordinates = [toll.coordinates for toll in toll_booths]
    center = GeographicUtils.calculate_centroid(all_coordinates)
    
    # Ajout de distances au centre pour chaque péage
    for toll in toll_booths:
        toll.distance_to_center_km = GeographicUtils.calculate_geodesic_distance(
            toll.coordinates, center
        ) / 1000.0
    
    # Clustering spatial des péages
    toll_coordinates = [toll.coordinates for toll in toll_booths]
    clusters = GeographicUtils.spatial_clustering(toll_coordinates)
    
    # Attribution des clusters
    for i, toll in enumerate(toll_booths):
        toll.spatial_cluster = clusters[i]
    
    return toll_booths, center, clusters

# Validation géographique des liaisons autoroutières
def validate_motorway_links_geography(complete_links):
    """Valide la géographie des liaisons autoroutières."""
    
    validation_results = []
    
    for link in complete_links:
        result = {
            'link_id': link.link_id,
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Validation des coordonnées
        if not GeographicUtils.validate_coordinates(link.entry_point.coordinates):
            result['errors'].append("Coordonnées d'entrée invalides")
            result['is_valid'] = False
        
        if not GeographicUtils.validate_coordinates(link.exit_point.coordinates):
            result['errors'].append("Coordonnées de sortie invalides")
            result['is_valid'] = False
        
        # Validation de la distance
        calculated_distance = GeographicUtils.calculate_geodesic_distance(
            link.entry_point.coordinates,
            link.exit_point.coordinates
        ) / 1000.0
        
        distance_diff = abs(calculated_distance - link.distance_km)
        if distance_diff > 5.0:  # Plus de 5km de différence
            result['warnings'].append(
                f"Distance incohérente: {calculated_distance:.1f}km vs {link.distance_km:.1f}km"
            )
        
        # Validation de la géométrie
        if len(link.geometry) < 2:
            result['warnings'].append("Géométrie insuffisante")
        else:
            polyline_length = GeographicUtils.calculate_polyline_length(link.geometry) / 1000.0
            geometry_diff = abs(polyline_length - link.distance_km)
            if geometry_diff > 2.0:  # Plus de 2km de différence
                result['warnings'].append(
                    f"Longueur géométrie incohérente: {polyline_length:.1f}km"
                )
        
        validation_results.append(result)
    
    return validation_results
```

## 📊 Performance et optimisation

### **Benchmarks typiques**
```python
# Performances des calculs géographiques (sur 1000 calculs)
performance_benchmarks = {
    "geodesic_distance": {
        "time_per_calculation": "0.15ms",
        "accuracy": "±1mm",
        "use_case": "Calculs précis longue distance"
    },
    "haversine_distance": {
        "time_per_calculation": "0.05ms", 
        "accuracy": "±0.5%",
        "use_case": "Calculs rapides moyenne distance"
    },
    "euclidean_distance": {
        "time_per_calculation": "0.01ms",
        "accuracy": "±5% courte distance",
        "use_case": "Approximations rapides"
    },
    "spatial_clustering": {
        "time_for_1000_points": "50-200ms",
        "scalability": "O(n log n)",
        "use_case": "Groupement géographique"
    }
}
```

### **Optimisations recommandées**
```python
# Recommandations d'usage selon le contexte
def choose_distance_method(coord1, coord2, precision_required="medium"):
    """Choisit la méthode de calcul de distance optimale."""
    
    distance_rough = GeographicUtils.calculate_euclidean_distance(coord1, coord2)
    
    if precision_required == "high" or distance_rough > 100000:  # >100km
        return GeographicUtils.calculate_geodesic_distance(coord1, coord2)
    elif precision_required == "medium" or distance_rough > 10000:  # >10km
        return GeographicUtils.calculate_haversine_distance(coord1, coord2)
    else:
        return distance_rough  # Euclidean sufficient for short distances

# Cache intelligent avec TTL
class GeographicCache:
    def __init__(self, ttl_seconds=3600):
        self.cache = {}
        self.timestamps = {}
        self.ttl = ttl_seconds
    
    def get_cached_result(self, cache_key):
        if cache_key in self.cache:
            if time.time() - self.timestamps[cache_key] < self.ttl:
                return self.cache[cache_key]
            else:
                # Expiration du cache
                del self.cache[cache_key]
                del self.timestamps[cache_key]
        return None
```