# 🔗 Cache Linking - Système de Liaison Autoroutière

## 📋 Vue d'ensemble

Le système de liaison autoroutière SAM connecte intelligemment les points d'entrée et de sortie des autoroutes pour créer des segments complets. Il utilise des algorithmes géospatiaux avancés pour construire un réseau cohérent de liaisons autoroutières avec association automatique des péages.

## 🏗️ Architecture

```
linking/
├── motorway_link_orchestrator.py    # Orchestrateur principal
├── link_builder.py                  # Construction des liaisons
├── coordinate_matcher.py            # Correspondance spatiale
├── coordinate_chain_builder.py      # Construction de chaînes de coordonnées
├── segment_chain_builder.py         # Construction de chaînes de segments
├── simple_chain_builder.py          # Constructeur de chaînes simplifiées
├── toll_detector.py                 # Détection de péages sur segments
└── __init__.py
```

## 🎯 Objectifs du système

### **Construction intelligente**
- 🔗 **Liaison automatique** : Connexion entrées/sorties par proximité spatiale
- 🧭 **Validation géométrique** : Vérification de cohérence des tracés
- 📏 **Calculs de distance** : Distances précises entre points de liaison
- 🎯 **Association péages** : Linking automatique péages ↔ segments

### **Performance et fiabilité**
- ⚡ **Algorithmes optimisés** : Complexité O(n log n) avec index spatiaux
- 🛡️ **Gestion des erreurs** : Traitement des cas d'orphelins et ambiguïtés
- 📊 **Statistiques détaillées** : Métriques de construction et validation
- 🔄 **Reproductibilité** : Résultats cohérents et déterministes

## 🧩 Composants détaillés

### **1. MotorwayLinkOrchestrator** - Orchestrateur Principal

Le composant central qui coordonne tout le processus de liaison autoroutière.

#### **Responsabilités**
- 🎭 **Orchestration** : Coordination des étapes de construction
- 📊 **Collecte de statistiques** : Métriques de performance
- 🔍 **Validation** : Contrôles de qualité des liaisons
- 💾 **Persistence** : Sauvegarde des résultats et diagnostics

#### **Processus de construction**
```python
from src.cache.linking.motorway_link_orchestrator import MotorwayLinkOrchestrator

# Initialisation
orchestrator = MotorwayLinkOrchestrator(
    max_distance_m=2.0,           # Distance max pour liaison (mètres)
    output_dir="osm_cache_test",  # Répertoire de sortie
    enable_statistics=True,        # Collecte de statistiques
    enable_validation=True         # Validation des résultats
)

# Construction des liaisons complètes
complete_links = orchestrator.build_complete_links(
    entries=motorway_entries,      # Points d'entrée
    exits=motorway_exits,          # Points de sortie
    indeterminates=indeterminates  # Points indéterminés (optionnel)
)

# Statistiques détaillées
stats = orchestrator.get_linking_statistics()
print(f"✅ {len(complete_links)} liaisons créées")
print(f"📊 Temps de traitement: {stats['processing_time_ms']}ms")
print(f"🎯 Taux de réussite: {stats['success_rate']:.1f}%")
```

#### **Métriques collectées**
```python
linking_statistics = {
    "input_counts": {
        "entries": 156,
        "exits": 142,
        "indeterminates": 23
    },
    "output_counts": {
        "complete_links": 134,
        "orphaned_entries": 8,
        "orphaned_exits": 12
    },
    "performance": {
        "processing_time_ms": 1247,
        "average_distance_m": 1.34,
        "success_rate": 89.3
    },
    "quality_metrics": {
        "geometric_validation_passed": 131,
        "distance_validation_passed": 134,
        "highway_ref_matches": 127
    }
}
```

---

### **2. LinkBuilder** - Constructeur de Liaisons

Composant spécialisé dans la création des liaisons entre points d'entrée et de sortie.

#### **Algorithme de liaison**
```python
from src.cache.linking.link_builder import LinkBuilder

# Initialisation
builder = LinkBuilder(max_distance_m=2.0)

# Construction des liaisons
def build_links(entries, exits):
    """
    Algorithme de liaison spatiale :
    1. Index spatial des points de sortie
    2. Pour chaque entrée, recherche des sorties proches
    3. Validation géométrique et sémantique
    4. Création des liaisons optimales
    """
    
    # Étape 1: Index spatial (Rtree)
    spatial_index = builder.create_spatial_index(exits)
    
    # Étape 2: Recherche et liaison
    links = []
    for entry in entries:
        candidates = builder.find_nearby_exits(entry, spatial_index)
        best_exit = builder.select_best_exit(entry, candidates)
        
        if best_exit:
            link = builder.create_complete_link(entry, best_exit)
            if builder.validate_link(link):
                links.append(link)
    
    return links
```

#### **Critères de sélection**
```python
def select_best_exit(entry, candidates):
    """Sélectionne la meilleure sortie pour une entrée."""
    
    scores = []
    for exit in candidates:
        score = 0
        
        # Distance (poids: 40%)
        distance_score = 1.0 - (distance_m / max_distance_m)
        score += distance_score * 0.4
        
        # Correspondance autoroute (poids: 30%)
        if entry.highway_ref == exit.highway_ref:
            score += 0.3
        
        # Cohérence géométrique (poids: 20%)
        geometric_score = calculate_geometric_coherence(entry, exit)
        score += geometric_score * 0.2
        
        # Correspondance opérateur (poids: 10%)
        if entry.operator == exit.operator:
            score += 0.1
        
        scores.append((exit, score))
    
    # Retourne la sortie avec le meilleur score
    return max(scores, key=lambda x: x[1])[0] if scores else None
```

---

### **3. CoordinateMatcher** - Correspondance Spatiale

Composant de correspondance spatiale haute performance utilisant des algorithmes géométriques optimisés.

#### **Fonctionnalités**
- 📍 **Recherche spatiale** : Rtree pour requêtes géospatiales
- 📏 **Calculs de distance** : Distances géodésiques précises
- 🧭 **Validation géométrique** : Cohérence des tracés
- 🎯 **Filtrage intelligent** : Élimination des correspondances aberrantes

#### **Utilisation**
```python
from src.cache.linking.coordinate_matcher import are_coordinates_equal, calculate_distance_meters

# Comparaison de coordonnées avec précision
point1 = [4.8345, 46.7123]
point2 = [4.8346, 46.7124]

are_equal = are_coordinates_equal(point1, point2, precision=6)
print(f"Coordonnées identiques (6 décimales): {are_equal}")

# Calcul de distance
distance_m = calculate_distance_meters(point1, point2)
print(f"Distance: {distance_m:.2f} mètres")
```

**Note**: Le module `coordinate_matcher` fournit des fonctions de base pour la correspondance spatiale. La classe `CoordinateMatcher` documentée ci-dessous représente une version étendue recommandée.

#### **Extension recommandée - CoordinateMatcher (classe)**

# Statistiques de correspondance
match_stats = matcher.get_matching_statistics()
print(f"Correspondances trouvées: {len(matches)}")
print(f"Correspondances validées: {len(validated_matches)}")
print(f"Taux de validation: {match_stats['validation_rate']:.1f}%")
```

#### **Algorithmes de distance**
```python
def calculate_precise_distance(coord1, coord2):
    """Calcule la distance géodésique précise entre deux points."""
    
    # Utilisation de pyproj pour précision maximale
    from pyproj import Geod
    
    geod = Geod(ellps='WGS84')
    azimuth1, azimuth2, distance = geod.inv(
        coord1[0], coord1[1],  # longitude, latitude point 1
        coord2[0], coord2[1]   # longitude, latitude point 2
    )
    
    return distance  # Distance en mètres

def calculate_geometric_coherence(entry, exit):
    """Évalue la cohérence géométrique d'une liaison."""
    
    # Angle de liaison
    bearing = calculate_bearing(entry.coordinates, exit.coordinates)
    
    # Cohérence avec la direction générale de l'autoroute
    highway_bearing = get_highway_bearing(entry.highway_ref)
    angle_diff = abs(bearing - highway_bearing)
    
    # Score de cohérence (0-1)
    coherence_score = 1.0 - (angle_diff / 180.0)
    
    return max(0.0, coherence_score)
```

---

### **4. ChainBuilders** - Constructeurs de Chaînes

Ensemble de composants pour la construction de chaînes de coordonnées et de segments.

#### **CoordinateChainBuilder**
```python
from src.cache.linking.coordinate_chain_builder import CoordinateChainBuilder

# Construction de chaînes de coordonnées
chain_builder = CoordinateChainBuilder()

# Création d'une chaîne continue
coordinate_chain = chain_builder.build_coordinate_chain(
    start_point=entry.coordinates,
    end_point=exit.coordinates,
    intermediate_points=segment_coordinates
)

# Validation de la chaîne
is_valid = chain_builder.validate_chain(coordinate_chain)
```

#### **SegmentChainBuilder**
```python
from src.cache.linking.segment_chain_builder import SegmentChainBuilder

# Construction de chaînes de segments
segment_builder = SegmentChainBuilder()

# Création d'une chaîne de segments
segment_chain = segment_builder.build_segment_chain(
    entry_link=entry,
    exit_link=exit,
    intermediate_segments=motorway_segments
)

# Calcul de la distance totale
total_distance = segment_builder.calculate_chain_distance(segment_chain)
```

---

### **5. TollDetector** - Détection de Péages

Composant spécialisé dans la détection et l'association de péages aux segments autoroutiers.

#### **Fonctionnalités**
- 🎯 **Détection spatiale** : Localisation des péages sur segments
- 📏 **Association par distance** : Liaison péages ↔ segments
- 🔍 **Validation contextuelle** : Vérification cohérence opérateur/autoroute
- 📊 **Statistiques d'association** : Métriques de succès

#### **Utilisation**
```python
from src.cache.linking.toll_detector import TollDetector

# Initialisation
detector = TollDetector(
    max_association_distance_m=1.5,  # Distance max pour association
    enable_operator_validation=True   # Validation opérateur
)

# Détection des péages sur un segment
associated_tolls = detector.detect_tolls_on_segment(
    segment=complete_motorway_link,
    available_tolls=all_toll_booths
)

# Association globale péages ↔ segments
toll_associations = detector.associate_tolls_to_segments(
    segments=complete_links,
    tolls=toll_booths
)

# Statistiques d'association
association_stats = detector.get_association_statistics()
print(f"Péages associés: {association_stats['associated_tolls']}")
print(f"Segments avec péages: {association_stats['segments_with_tolls']}")
```

#### **Algorithme d'association**
```python
def associate_tolls_to_segments(segments, tolls):
    """Associe les péages aux segments autoroutiers."""
    
    associations = []
    
    for segment in segments:
        segment_tolls = []
        
        for toll in tolls:
            # Vérification de proximité spatiale
            if is_toll_near_segment(toll, segment):
                
                # Validation contextuelle
                if validate_toll_segment_match(toll, segment):
                    segment_tolls.append(toll.osm_id)
        
        # Association segment ↔ péages
        if segment_tolls:
            associations.append({
                'segment_id': segment.link_id,
                'associated_tolls': segment_tolls,
                'toll_count': len(segment_tolls)
            })
    
    return associations

def is_toll_near_segment(toll, segment):
    """Vérifie si un péage est proche d'un segment."""
    
    # Distance point-segment minimum
    min_distance = float('inf')
    
    for i in range(len(segment.geometry) - 1):
        point1 = segment.geometry[i]
        point2 = segment.geometry[i + 1]
        
        # Distance point-segment
        distance = point_to_line_distance(
            toll.coordinates, point1, point2
        )
        
        min_distance = min(min_distance, distance)
    
    return min_distance <= max_association_distance_m
```

## 🔧 Configuration et optimisation

### **Configuration globale**
```python
# Configuration du système de liaison
LINKING_CONFIG = {
    "max_distance_m": 2.0,              # Distance max liaison (mètres)
    "coordinate_precision": 6,           # Précision coordonnées (décimales)
    "enable_geometric_validation": True, # Validation géométrique
    "enable_operator_validation": True,  # Validation opérateur
    "max_association_distance_m": 1.5,   # Distance max association péages
    "enable_statistics": True,           # Collecte statistiques
    "debug_mode": False,                 # Mode debug avec logs détaillés
    "output_orphaned_segments": True     # Sauvegarde segments orphelins
}

# Application de la configuration
orchestrator = MotorwayLinkOrchestrator(**LINKING_CONFIG)
```

### **Optimisations de performance**
```python
# Index spatial avec cache
class OptimizedSpatialIndex:
    def __init__(self):
        self._cache = {}
        self._rtree_index = rtree.index.Index()
    
    def query_with_cache(self, bbox):
        """Requête spatiale avec cache."""
        cache_key = hash(tuple(bbox))
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        results = list(self._rtree_index.intersection(bbox))
        self._cache[cache_key] = results
        
        return results

# Traitement parallèle pour gros volumes
async def build_links_parallel(entries, exits, batch_size=100):
    """Construction de liaisons en parallèle."""
    
    import asyncio
    
    # Division en lots
    batches = [entries[i:i+batch_size] for i in range(0, len(entries), batch_size)]
    
    # Traitement parallèle
    tasks = [
        asyncio.create_task(process_batch(batch, exits))
        for batch in batches
    ]
    
    # Collecte des résultats
    batch_results = await asyncio.gather(*tasks)
    
    # Fusion des résultats
    all_links = []
    for batch_links in batch_results:
        all_links.extend(batch_links)
    
    return all_links
```

## 📊 Métriques et validation

### **Métriques de performance typiques**
```python
# Temps de traitement (pour ~300 points)
performance_metrics = {
    "spatial_indexing": "50-100ms",
    "distance_calculations": "200-400ms", 
    "link_building": "300-600ms",
    "toll_association": "100-200ms",
    "validation": "100-150ms",
    "total_processing": "750-1450ms"
}

# Ratios de succès typiques
success_metrics = {
    "linking_success_rate": "85-95%",     # Pourcentage de liaisons créées
    "geometric_validation": "90-98%",     # Validation géométrique
    "toll_association_rate": "75-85%",    # Péages associés avec succès
    "operator_consistency": "80-90%"      # Cohérence opérateur
}
```

### **Validation des résultats**
```python
def validate_linking_results(complete_links):
    """Valide les résultats de liaison."""
    
    validation_report = {
        "total_links": len(complete_links),
        "validation_errors": [],
        "warnings": [],
        "quality_score": 0.0
    }
    
    for link in complete_links:
        # Validation distance
        if link.distance_km <= 0:
            validation_report["validation_errors"].append(
                f"Distance invalide pour {link.link_id}"
            )
        
        # Validation géométrie
        if len(link.geometry) < 2:
            validation_report["warnings"].append(
                f"Géométrie insuffisante pour {link.link_id}"
            )
        
        # Validation références
        if not link.highway_ref:
            validation_report["warnings"].append(
                f"Référence autoroute manquante pour {link.link_id}"
            )
    
    # Calcul du score de qualité
    error_count = len(validation_report["validation_errors"])
    warning_count = len(validation_report["warnings"])
    total_links = validation_report["total_links"]
    
    if total_links > 0:
        validation_report["quality_score"] = (
            (total_links - error_count - warning_count * 0.5) / total_links
        ) * 100
    
    return validation_report
```
