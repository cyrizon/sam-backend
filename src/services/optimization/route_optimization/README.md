# 🎯 Route Optimization - Moteur d'Optimisation d'Itinéraires

## 📋 Vue d'ensemble

Le module `route_optimization` implémente le moteur principal d'optimisation d'itinéraires de SAM. Il utilise une architecture modulaire en 8 étapes pour analyser, optimiser et assembler des itinéraires sous contraintes de péages et de budget.

## 🏗️ Architecture modulaire

```
src/services/optimization/route_optimization/
├── 📁 main/                        # Orchestrateurs principaux
│   └── intelligent_optimizer.py   # Orchestrateur intelligent principal
├── 📁 route_handling/              # Gestion des routes de base
│   ├── base_route_provider.py     # Fournisseur de routes de base
│   └── tollway_processor.py       # Traitement des sections à péages
├── 📁 toll_analysis/               # Analyse et sélection des péages
│   ├── toll_identifier.py         # Identification des péages sur route
│   ├── toll_selector.py           # Sélection intelligente des péages
│   ├── 📁 spatial/                # Index et calculs spatiaux
│   ├── 📁 detection/              # Détection et classification
│   ├── 📁 utils/                  # Utilitaires d'analyse
│   └── 📁 verification/           # Vérification géométrique
├── 📁 segmentation/                # Segmentation et calculs
│   ├── segment_creator.py         # Création de segments d'évitement
│   └── segment_calculator.py      # Calcul des routes alternatives
├── 📁 assembly/                    # Assemblage final
│   └── route_assembler.py         # Assemblage des résultats finaux
└── 📁 utils/                      # Utilitaires partagés
    ├── cache_accessor.py          # Accès aux données de cache
    └── route_extractor.py         # Extraction de données de route
```

## 🔄 Pipeline d'optimisation (8 étapes)

### **Étape 1-2 : Fourniture de routes de base**
**Module** : `route_handling/base_route_provider.py`

```python
from src.services.optimization.route_optimization.route_handling.base_route_provider import BaseRouteProvider

provider = BaseRouteProvider(ors_service)

# Étape 1 : Route de base avec informations de péages
base_route = provider.get_base_route(coordinates)
print(f"Route de base : {base_route['distance']/1000:.1f}km, {base_route['duration']/3600:.1f}h")

# Étape 2 : Route alternative sans péages
no_toll_route = provider.get_no_toll_route(coordinates)  
print(f"Route sans péages : {no_toll_route['distance']/1000:.1f}km")
```

**Fonctionnalités** :
- 🔌 **Appels ORS optimisés** : Requêtes avec paramètres adaptés
- 📊 **Extraction des données** : Géométrie, distance, durée, informations péages
- ✅ **Validation** : Contrôle de la cohérence des réponses ORS
- 🛡️ **Gestion d'erreurs** : Récupération gracieuse en cas d'échec

---

### **Étape 3 : Identification des péages**
**Module** : `toll_analysis/toll_identifier.py`

```python
from src.services.optimization.route_optimization.toll_analysis.toll_identifier import TollIdentifier

identifier = TollIdentifier()

# Identification des péages sur la route de base
tolls_on_route = identifier.identify_tolls_on_route(
    route_geometry=base_route['geometry'],
    route_coordinates=base_route['coordinates']
)

print(f"Péages détectés : {len(tolls_on_route)}")
for toll in tolls_on_route:
    print(f"  - {toll.name} ({toll.operator}) : {toll.toll_type}")
```

**Algorithmes utilisés** :
- 🗺️ **Analyse spatiale** : Détection par intersection géométrique
- 📏 **Calculs de distance** : Buffer de détection configurable (80m)
- 🔍 **Index spatial** : Rtree pour performances optimales
- 🎯 **Classification** : Péages ouverts vs fermés

---

### **Étape 4 : Analyse interne des contraintes**
**Logique intégrée** dans `intelligent_optimizer.py`

```python
# Évaluation automatique des contraintes
if len(tolls_on_route) <= target_tolls:
    # Contrainte respectée, optimisation simple
    return simple_optimization_result
else:
    # Nécessité d'éviter certains péages
    continue_to_step_5()
```

---

### **Étape 5 : Sélection des péages à éviter**
**Module** : `toll_analysis/toll_selector.py`

```python
from src.services.optimization.route_optimization.toll_analysis.toll_selector import TollSelector

selector = TollSelector()

# Sélection intelligente des péages à éviter
selected_tolls = selector.select_tolls_to_avoid(
    available_tolls=tolls_on_route,
    target_count=target_tolls,
    optimization_mode='count',  # ou 'budget'
    veh_class="c1"
)

print(f"Péages sélectionnés pour évitement : {len(selected_tolls)}")
```

**Stratégies de sélection** :
- 💰 **Par coût** : Éviter les péages les plus chers en premier
- 📊 **Par impact** : Minimiser l'impact sur le temps de trajet
- 🎯 **Par combinaisons** : Tester différentes combinaisons d'évitement
- 🧠 **Algorithmes intelligents** : Sélection adaptative selon le contexte

---

### **Étape 6 : Création de segments d'évitement**
**Module** : `segmentation/segment_creator.py`

```python
from src.services.optimization.route_optimization.segmentation.segment_creator import SegmentCreator

creator = SegmentCreator()

# Création des segments avec polygones d'évitement
avoidance_segments = creator.create_avoidance_segments(
    tolls_to_avoid=selected_tolls,
    base_route_geometry=base_route['geometry']
)

for segment in avoidance_segments:
    print(f"Segment d'évitement : {segment.polygon_area:.0f}m² autour de {segment.toll_name}")
```

**Techniques utilisées** :
- 🔺 **Polygones d'évitement** : Zones géométriques autour des péages
- 📐 **Calculs géométriques** : Buffers adaptatifs selon le type de péage
- 🗺️ **Optimisation spatiale** : Polygones minimaux pour évitement efficace
- 🔗 **Combinaisons intelligentes** : Fusion de polygones proches

---

### **Étape 7 : Calcul des routes alternatives**
**Module** : `segmentation/segment_calculator.py`

```python
from src.services.optimization.route_optimization.segmentation.segment_calculator import SegmentCalculator

calculator = SegmentCalculator(ors_service)

# Calcul des routes alternatives avec évitement
alternative_routes = calculator.calculate_alternative_routes(
    original_coordinates=coordinates,
    avoidance_segments=avoidance_segments
)

for route in alternative_routes:
    print(f"Route alternative : {route['distance']/1000:.1f}km, coût: {route['estimated_cost']:.2f}€")
```

**Fonctionnalités** :
- 🔌 **Appels ORS avec polygones** : Évitement géométrique précis
- 💰 **Estimation des coûts** : Calcul automatique des tarifs
- ⏱️ **Calculs parallèles** : Traitement simultané des alternatives
- 📊 **Métriques de qualité** : Évaluation de chaque alternative

---

### **Étape 8 : Assemblage des résultats finaux**
**Module** : `assembly/route_assembler.py`

```python
from src.services.optimization.route_optimization.assembly.route_assembler import RouteAssembler

assembler = RouteAssembler()

# Assemblage final avec toutes les alternatives
final_result = assembler.assemble_final_results(
    base_route=base_route,
    no_toll_route=no_toll_route,
    alternative_routes=alternative_routes,
    optimization_context={
        'target_tolls': target_tolls,
        'veh_class': veh_class,
        'optimization_mode': optimization_mode
    }
)

# Résultat structuré
print(f"Statut : {final_result['status']}")
print(f"Route la plus rapide : {final_result['fastest']['duration']/3600:.1f}h")
print(f"Route la moins chère : {final_result['cheapest']['cost']:.2f}€")
print(f"Route min péages : {final_result['min_tolls']['toll_count']} péages")
```

**Logique d'assemblage** :
- 🏆 **Sélection des meilleures** : Fastest, cheapest, min_tolls
- 📊 **Calculs de métriques** : Coûts, durées, distances précises
- ✅ **Validation finale** : Vérification de la cohérence
- 📈 **Métriques de performance** : Statistiques d'optimisation

## 🧩 Modules de support

### **Analyse spatiale avancée**
**Module** : `toll_analysis/spatial/spatial_index.py`

```python
from src.services.optimization.route_optimization.toll_analysis.spatial.spatial_index import SpatialIndex

# Index spatial pour performances optimales
spatial_index = SpatialIndex()
spatial_index.build_index(toll_booths)

# Recherche rapide de péages proches
nearby_tolls = spatial_index.find_tolls_near_route(
    route_geometry=route_coordinates,
    buffer_distance=80.0
)
```

### **Vérification géométrique**
**Module** : `toll_analysis/verification/shapely_verifier.py`

```python
from src.services.optimization.route_optimization.toll_analysis.verification.shapely_verifier import ShapelyVerifier

verifier = ShapelyVerifier()

# Vérification précise de l'intersection route-péage
intersection_result = verifier.verify_toll_on_route(
    route_geometry=route_linestring,
    toll_point=toll_coordinates,
    buffer_meters=80.0
)

if intersection_result.intersects:
    print(f"Intersection confirmée à {intersection_result.distance:.1f}m")
```

### **Accès aux données de cache**
**Module** : `utils/cache_accessor.py`

```python
from src.services.optimization.route_optimization.utils.cache_accessor import CacheAccessor

# Interface simplifiée pour l'accès aux données
cache = CacheAccessor()

# Accès aux péages et tarifs
toll_booths = cache.get_toll_booths()
operators_pricing = cache.get_operators_pricing()

# Recherche optimisée
toll_by_name = cache.find_toll_by_name("Fontaine Larivière")
nearby_tolls = cache.find_tolls_near_point(longitude, latitude, radius=1000)
```

## 🎯 Points d'intégration

### **Utilisation depuis SmartRouteService**
```python
# Le SmartRouteService utilise directement l'IntelligentOptimizer
from src.services.smart_route import SmartRouteService

smart_route = SmartRouteService()
# → Initialise automatiquement IntelligentOptimizer
# → Pipeline complet en 8 étapes
# → Résultats assemblés et optimisés
```

### **Utilisation directe de l'optimiseur**
```python
from src.services.optimization.route_optimization.main.intelligent_optimizer import IntelligentOptimizer
from src.services.ors_service import ORSService

ors_service = ORSService()
optimizer = IntelligentOptimizer(ors_service)

# Pipeline complet avec contrôle fin
result = optimizer.find_optimized_route(
    coordinates=[[4.8345, 46.7123], [2.3522, 48.8566]],
    target_tolls=2,
    optimization_mode='count',
    veh_class="c1"
)
```

### **Utilisation de modules individuels**
```python
# Utilisation modulaire pour cas spécifiques
from src.services.optimization.route_optimization.toll_analysis.toll_identifier import TollIdentifier
from src.services.optimization.route_optimization.route_handling.base_route_provider import BaseRouteProvider

# Seulement identification de péages
identifier = TollIdentifier()
tolls = identifier.identify_tolls_on_route(route_geometry, route_coordinates)

# Seulement fourniture de routes
provider = BaseRouteProvider(ors_service)
base_route = provider.get_base_route(coordinates)
```