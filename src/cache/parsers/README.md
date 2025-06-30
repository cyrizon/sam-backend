# 📄 Cache Parsers - Parseurs de Données

## 📋 Vue d'ensemble

Les parseurs du cache SAM sont responsables de la lecture, validation et transformation des données externes en modèles internes utilisables. Ils supportent multiple formats de données (GeoJSON, CSV, JSON) et sources (OSM, opérateurs, fichiers personnalisés).

## 🏗️ Architecture

```
parsers/
├── toll_booth_parser.py           # Parseur de péages OSM
├── motorway_link_parser.py        # Parseur de liaisons autoroutières
├── motorway_segments_parser.py    # Parseur de segments autoroutiers
├── multi_source_parser.py         # Parseur multi-sources
└── __init__.py
```

## 🎯 Objectifs des parseurs

### **Flexibilité des formats**
- 📊 **Multi-formats** : GeoJSON, CSV, JSON, XML support
- 🔄 **Transformation** : Conversion vers modèles internes uniformes
- ✅ **Validation** : Contrôles de cohérence et d'intégrité
- 🌍 **Encoding** : Support UTF-8, encodages locaux

### **Robustesse**
- 🛡️ **Gestion d'erreurs** : Traitement gracieux des données malformées
- 📊 **Statistiques** : Métriques de parsing et validation
- 🔄 **Récupération** : Stratégies de fallback et retry
- 📝 **Logging** : Traçabilité des opérations

## 🧩 Composants détaillés

### **1. TollBoothParser** - Parseur de Péages

Parseur spécialisé pour les stations de péages depuis les données OSM.

#### **Fonctionnalités**
- 🗺️ **Format OSM** : Lecture des données OpenStreetMap (GeoJSON)
- 🏷️ **Enrichissement** : Ajout de métadonnées et classification
- 🎯 **Filtrage** : Sélection par critères (opérateur, autoroute, type)
- 📊 **Validation** : Contrôles de cohérence géographique

#### **Utilisation**
```python
from src.cache.parsers.toll_booth_parser import TollBoothParser

# Initialisation
parser = TollBoothParser(
    data_dir="./data",
    enable_validation=True,
    enable_enrichment=True
)

# Parsing des péages depuis GeoJSON
toll_booths = parser.parse_toll_booths_from_geojson(
    file_path="./data/osm/toll_stations.geojson"
)

print(f"✅ {len(toll_booths)} péages parsés")

# Statistiques de parsing
stats = parser.get_parsing_statistics()
print(f"📊 Statistiques:")
print(f"   - Péages valides: {stats['valid_tolls']}")
print(f"   - Péages rejetés: {stats['rejected_tolls']}")
print(f"   - Péages ouverts: {stats['open_tolls']}")
print(f"   - Péages fermés: {stats['closed_tolls']}")
```

#### **Structure GeoJSON attendue**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "highway": "toll_booth",
        "barrier": "toll_booth",
        "name": "Péage de Fontaine Larivière",
        "operator": "ASF",
        "operator:ref": "FL001",
        "ref": "A 6",
        "toll": "yes",
        "toll:type": "open"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [4.8567, 46.7892]
      }
    }
  ]
}
```

#### **Enrichissement automatique**
```python
def enrich_toll_booth_data(self, toll_data):
    """Enrichit les données de péage avec des informations déduites."""
    
    enriched_data = toll_data.copy()
    
    # Détection du type de péage
    if "toll:type" in toll_data.get("properties", {}):
        toll_type = toll_data["properties"]["toll:type"]
        enriched_data["toll_type"] = "O" if toll_type == "open" else "F"
    else:
        # Déduction basée sur l'opérateur et le nom
        if self.is_likely_open_toll(toll_data):
            enriched_data["toll_type"] = "O"
        else:
            enriched_data["toll_type"] = "F"
    
    # Normalisation du nom d'opérateur
    operator = toll_data.get("properties", {}).get("operator", "")
    enriched_data["operator"] = self.normalize_operator_name(operator)
    
    # Extraction de la référence d'autoroute
    highway_ref = toll_data.get("properties", {}).get("ref", "")
    enriched_data["highway_ref"] = self.normalize_highway_ref(highway_ref)
    
    # Ajout de métadonnées géographiques
    coords = toll_data["geometry"]["coordinates"]
    enriched_data["geographic_info"] = {
        "department": self.get_department_from_coordinates(coords),
        "region": self.get_region_from_coordinates(coords)
    }
    
    return enriched_data
```

---

### **2. MotorwayLinkParser** - Parseur de Liaisons Autoroutières

Parseur pour les points d'entrée et sortie des autoroutes.

#### **Responsabilités**
- 🛣️ **Points de liaison** : Entrées et sorties autoroutières
- 🔍 **Classification** : Détermination du type (entrée/sortie/indéterminé)
- 📍 **Géolocalisation** : Validation des coordonnées
- 🏷️ **Métadonnées** : Enrichissement avec informations contextuelles

#### **Utilisation**
```python
from src.cache.parsers.motorway_link_parser import MotorwayLinkParser

# Initialisation
parser = MotorwayLinkParser(
    data_dir="./data",
    classification_enabled=True
)

# Parsing des liens autoroutiers
parsing_result = parser.parse_motorway_links(
    file_path="./data/osm/motorway_links.geojson"
)

entries = parsing_result['entries']
exits = parsing_result['exits'] 
indeterminates = parsing_result['indeterminates']

print(f"✅ Parsing terminé:")
print(f"   - Entrées: {len(entries)}")
print(f"   - Sorties: {len(exits)}")
print(f"   - Indéterminés: {len(indeterminates)}")
```

#### **Algorithme de classification**
```python
def classify_motorway_link(self, link_data):
    """Classifie un lien autoroutier en entrée/sortie."""
    
    properties = link_data.get("properties", {})
    
    # Classification basée sur les tags OSM
    if "highway" in properties:
        highway_type = properties["highway"]
        
        if highway_type == "motorway_link":
            # Analyse des tags additionnels
            if "destination" in properties:
                return LinkType.EXIT  # Sortie vers destination
            elif "source" in properties:
                return LinkType.ENTRY  # Entrée depuis source
            elif "oneway" in properties:
                oneway = properties["oneway"]
                if oneway == "yes":
                    # Analyse de la direction basée sur la géométrie
                    return self.classify_by_geometry(link_data)
                else:
                    return LinkType.INDETERMINATE
    
    # Classification par analyse géométrique
    return self.classify_by_geometric_analysis(link_data)

def classify_by_geometric_analysis(self, link_data):
    """Classification basée sur l'analyse géométrique."""
    
    coordinates = link_data["geometry"]["coordinates"]
    
    if len(coordinates) < 2:
        return LinkType.INDETERMINATE
    
    # Calcul de l'orientation
    start_coord = coordinates[0]
    end_coord = coordinates[-1]
    
    bearing = self.calculate_bearing(start_coord, end_coord)
    
    # Analyse de la proximité aux autoroutes principales
    nearest_motorway = self.find_nearest_motorway(start_coord)
    
    if nearest_motorway:
        motorway_bearing = nearest_motorway.get_bearing()
        angle_diff = abs(bearing - motorway_bearing)
        
        # Logique de classification basée sur l'angle
        if angle_diff < 45:  # Même direction générale
            return LinkType.ENTRY
        elif angle_diff > 135:  # Direction opposée
            return LinkType.EXIT
        else:
            return LinkType.INDETERMINATE
    
    return LinkType.INDETERMINATE
```

---

### **3. MotorwaySegmentsParser** - Parseur de Segments Autoroutiers

Parseur pour les segments complets d'autoroutes avec géométries détaillées.

#### **Fonctionnalités**
- 🛣️ **Segments complets** : Parsing des tronçons autoroutiers
- 📏 **Calculs géométriques** : Distances et orientations
- 🏷️ **Métadonnées** : Opérateurs, références, caractéristiques
- 🔗 **Préparation liaison** : Données pour le système de linking

#### **Utilisation**
```python
from src.cache.parsers.motorway_segments_parser import MotorwaySegmentsParser

# Initialisation
parser = MotorwaySegmentsParser(
    data_dir="./data",
    calculate_distances=True,
    simplify_geometry=True,
    tolerance_m=10.0
)

# Parsing des segments
segments = parser.parse_motorway_segments(
    file_path="./data/osm/motorway_segments.geojson"
)

print(f"✅ {len(segments)} segments parsés")

# Analyse des segments
analysis = parser.analyze_segments(segments)
print(f"📊 Analyse:")
print(f"   - Distance totale: {analysis['total_distance_km']:.1f} km")
print(f"   - Opérateurs: {len(analysis['operators'])}")
print(f"   - Autoroutes: {len(analysis['highways'])}")
```

#### **Traitement des géometries**
```python
def process_segment_geometry(self, segment_data):
    """Traite la géométrie d'un segment autoroutier."""
    
    geometry = segment_data["geometry"]
    coordinates = geometry["coordinates"]
    
    processed_segment = {
        "original_geometry": geometry,
        "coordinates": coordinates,
        "geometry_info": {}
    }
    
    # Calcul de la distance
    if self.calculate_distances:
        distance_m = self.calculate_polyline_distance(coordinates)
        processed_segment["distance_km"] = distance_m / 1000.0
        processed_segment["geometry_info"]["distance_m"] = distance_m
    
    # Simplification de la géométrie si demandée
    if self.simplify_geometry and self.tolerance_m > 0:
        simplified_coords = self.simplify_coordinates(
            coordinates, self.tolerance_m
        )
        processed_segment["simplified_geometry"] = {
            "type": "LineString",
            "coordinates": simplified_coords
        }
        processed_segment["geometry_info"]["simplification_ratio"] = (
            len(simplified_coords) / len(coordinates)
        )
    
    # Calcul des bearings
    if len(coordinates) >= 2:
        start_bearing = self.calculate_bearing(coordinates[0], coordinates[1])
        end_bearing = self.calculate_bearing(coordinates[-2], coordinates[-1])
        
        processed_segment["geometry_info"]["start_bearing"] = start_bearing
        processed_segment["geometry_info"]["end_bearing"] = end_bearing
        processed_segment["geometry_info"]["bearing_change"] = (
            self.angle_difference(start_bearing, end_bearing)
        )
    
    # Calcul de la bounding box
    bbox = self.calculate_bounding_box(coordinates)
    processed_segment["bbox"] = bbox
    
    return processed_segment
```

---

### **4. MultiSourceParser** - Parseur Multi-Sources

Parseur unifié capable de traiter multiple sources et formats de données.

#### **Fonctionnalités**
- 🔄 **Multi-formats** : GeoJSON, CSV, JSON, XML
- 📊 **Agrégation** : Fusion de données de sources multiples
- 🔍 **Déduplication** : Élimination des doublons
- 🎯 **Mapping** : Correspondance entre schémas différents

#### **Utilisation**
```python
from src.cache.parsers.multi_source_parser import MultiSourceParser

# Configuration des sources
sources_config = {
    "osm_tolls": {
        "file_path": "./data/osm/toll_stations.geojson",
        "format": "geojson",
        "parser": "toll_booth",
        "priority": 1
    },
    "operator_data": {
        "file_path": "./data/operators/toll_details.csv",
        "format": "csv",
        "parser": "toll_booth",
        "priority": 2
    },
    "custom_additions": {
        "file_path": "./data/custom/additional_tolls.json",
        "format": "json",
        "parser": "toll_booth",
        "priority": 3
    }
}

# Initialisation
parser = MultiSourceParser(
    sources_config=sources_config,
    enable_deduplication=True,
    enable_validation=True
)

# Parsing multi-sources
result = parser.parse_all_sources()

merged_data = result['merged_data']
source_stats = result['source_statistics']
conflicts = result['conflicts']

print(f"✅ Parsing multi-sources terminé:")
print(f"   - Éléments fusionnés: {len(merged_data)}")
print(f"   - Sources traitées: {len(source_stats)}")
print(f"   - Conflits détectés: {len(conflicts)}")
```

#### **Algorithme de fusion**
```python
def merge_data_sources(self, sources_data):
    """Fusionne les données de sources multiples."""
    
    merged_data = {}
    conflicts = []
    
    # Tri par priorité
    sorted_sources = sorted(
        sources_data.items(),
        key=lambda x: x[1]['priority']
    )
    
    for source_name, source_data in sorted_sources:
        for item_id, item_data in source_data['data'].items():
            
            if item_id not in merged_data:
                # Première occurrence
                merged_data[item_id] = {
                    'data': item_data,
                    'source': source_name,
                    'sources': [source_name]
                }
            else:
                # Conflit potentiel
                existing_data = merged_data[item_id]['data']
                
                if self.data_conflicts(existing_data, item_data):
                    conflicts.append({
                        'item_id': item_id,
                        'source1': merged_data[item_id]['source'],
                        'source2': source_name,
                        'data1': existing_data,
                        'data2': item_data
                    })
                    
                    # Résolution du conflit basée sur la priorité
                    if source_data['priority'] < merged_data[item_id]['priority']:
                        merged_data[item_id]['data'] = item_data
                        merged_data[item_id]['source'] = source_name
                
                # Ajout de la source à la liste
                merged_data[item_id]['sources'].append(source_name)
    
    return merged_data, conflicts

def data_conflicts(self, data1, data2):
    """Détecte les conflits entre deux ensembles de données."""
    
    # Champs critiques à vérifier
    critical_fields = ['coordinates', 'operator', 'name', 'toll_type']
    
    for field in critical_fields:
        if field in data1 and field in data2:
            if data1[field] != data2[field]:
                # Conflit détecté
                return True
    
    return False
```

## 🔧 Configuration et validation

### **Configuration globale des parseurs**
```python
# Configuration complète des parseurs
PARSERS_CONFIG = {
    "toll_booth_parser": {
        "enable_validation": True,
        "enable_enrichment": True,
        "coordinate_precision": 6,
        "required_fields": ["name", "coordinates", "operator"],
        "default_toll_type": "F"
    },
    "motorway_link_parser": {
        "classification_enabled": True,
        "geometric_analysis": True,
        "bearing_tolerance": 45.0,
        "distance_threshold_m": 500.0
    },
    "motorway_segments_parser": {
        "calculate_distances": True,
        "simplify_geometry": True,
        "tolerance_m": 10.0,
        "min_segment_length_m": 100.0
    },
    "multi_source_parser": {
        "enable_deduplication": True,
        "enable_validation": True,
        "conflict_resolution": "priority",
        "max_sources": 10
    }
}
```

### **Validation des données parsées**
```python
def validate_parsed_data(parsed_data, data_type):
    """Valide les données parsées selon le type."""
    
    validation_rules = {
        "toll_booth": {
            "required_fields": ["osm_id", "coordinates", "operator"],
            "coordinate_range": {"lon": [-180, 180], "lat": [-90, 90]},
            "operator_whitelist": ["ASF", "APRR", "SANEF", "AREA", "COFIROUTE"]
        },
        "motorway_link": {
            "required_fields": ["osm_id", "coordinates", "link_type"],
            "link_types": ["entry", "exit", "indeterminate"],
            "min_coordinates": 2
        },
        "motorway_segment": {
            "required_fields": ["osm_id", "geometry", "highway_ref"],
            "min_geometry_points": 2,
            "max_distance_km": 1000.0
        }
    }
    
    rules = validation_rules.get(data_type, {})
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "validated_count": 0,
        "total_count": len(parsed_data)
    }
    
    for item in parsed_data:
        item_errors = []
        
        # Validation des champs requis
        for field in rules.get("required_fields", []):
            if field not in item or item[field] is None:
                item_errors.append(f"Champ requis manquant: {field}")
        
        # Validation spécifique par type
        if data_type == "toll_booth":
            item_errors.extend(validate_toll_booth_specific(item, rules))
        elif data_type == "motorway_link":
            item_errors.extend(validate_motorway_link_specific(item, rules))
        elif data_type == "motorway_segment":
            item_errors.extend(validate_motorway_segment_specific(item, rules))
        
        if item_errors:
            validation_result["errors"].extend(item_errors)
            validation_result["is_valid"] = False
        else:
            validation_result["validated_count"] += 1
    
    return validation_result
```

## 📊 Métriques et monitoring

### **Statistiques de parsing**
```python
def collect_parsing_statistics(parser_results):
    """Collecte les statistiques de parsing."""
    
    stats = {
        "parsing_time_ms": parser_results.get("parsing_time_ms", 0),
        "total_items": parser_results.get("total_items", 0),
        "valid_items": parser_results.get("valid_items", 0),
        "rejected_items": parser_results.get("rejected_items", 0),
        "enriched_items": parser_results.get("enriched_items", 0),
        "success_rate": 0.0,
        "enrichment_rate": 0.0,
        "processing_speed": 0.0  # items/second
    }
    
    if stats["total_items"] > 0:
        stats["success_rate"] = (stats["valid_items"] / stats["total_items"]) * 100
        stats["enrichment_rate"] = (stats["enriched_items"] / stats["total_items"]) * 100
    
    if stats["parsing_time_ms"] > 0:
        stats["processing_speed"] = stats["total_items"] / (stats["parsing_time_ms"] / 1000.0)
    
    return stats
```

### **Monitoring des erreurs**
```python
def monitor_parsing_errors(error_log):
    """Analyse et catégorise les erreurs de parsing."""
    
    error_categories = {
        "format_errors": [],
        "validation_errors": [],
        "geographic_errors": [],
        "encoding_errors": [],
        "unknown_errors": []
    }
    
    for error in error_log:
        error_type = classify_error(error)
        error_categories[error_type].append(error)
    
    return {
        "total_errors": len(error_log),
        "error_categories": error_categories,
        "most_common_error": find_most_common_error(error_log),
        "error_rate": calculate_error_rate(error_log)
    }
```