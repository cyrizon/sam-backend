# 🎛️ Cache Managers - Gestionnaires de Cache

## 📋 Vue d'ensemble

Les gestionnaires de cache sont les orchestrateurs principaux du système de données SAM. Ils coordonnent le chargement, la validation et l'accès aux données géospatiales, tarifs et liaisons autoroutières.

## 🏗️ Architecture

```
managers/
├── cache_manager_with_linking.py    # Gestionnaire principal avec liaisons
├── cache_manager_with_pricing.py    # Gestionnaire avec tarification
├── osm_data_manager.py              # Données OpenStreetMap
├── open_tolls_manager.py            # Péages ouverts spécialisés
└── __init__.py
```

## 🧩 Composants détaillés

### **1. CacheManagerWithLinking** - Gestionnaire Principal

Le gestionnaire le plus complet qui hérite de toutes les fonctionnalités et ajoute la liaison autoroutière.

#### **Fonctionnalités clés**
- 🔗 **Liaison autoroutière** : Construction de segments complets
- 🎯 **Association péages** : Liaison péages ↔ segments
- 📊 **Statistiques complètes** : Métriques de performance
- 💰 **Intégration tarifaire** : Calculs de coûts avancés

#### **Utilisation**
```python
from src.cache.managers.cache_manager_with_linking import CacheManagerWithLinking

# Initialisation
cache = CacheManagerWithLinking(
    data_dir="./data",
    cache_dir="osm_cache_test"
)

# Chargement complet avec liaisons
success = cache.load_all_including_motorway_linking()

if success:
    # Accès aux données complètes
    toll_booths = cache.toll_booths                    # Péages complets
    complete_links = cache.complete_motorway_links      # Liaisons autoroutières
    operators = cache.get_available_operators()        # Opérateurs tarifaires
    
    # Statistiques détaillées
    stats = cache.get_linking_statistics()
    print(f"Liaisons créées: {stats['complete_links_created']}")
    print(f"Péages associés: {stats['tolls_associated']}")
```

#### **Processus de chargement**
```python
def load_all_including_motorway_linking(self) -> bool:
    """
    Processus complet de chargement :
    1. Chargement des données de base (péages, tarifs)
    2. Parsing des segments autoroutiers
    3. Construction des liaisons entrée/sortie
    4. Association des péages aux segments
    5. Validation et statistiques
    """
```

#### **Propriétés disponibles**
```python
# Collections de données
cache.toll_booths: List[TollBoothStation]           # Tous les péages
cache.complete_motorway_links: List[CompleteMotorwayLink]  # Liaisons complètes
cache.motorway_entries: List[MotorwayLink]          # Entrées autoroutières
cache.motorway_exits: List[MotorwayLink]            # Sorties autoroutières

# Services intégrés
cache.linking_orchestrator: MotorwayLinkOrchestrator
cache.toll_association_service: TollAssociationService
cache.links_serializer: CompleteMotorwayLinksSerializer

# États
cache.links_built: bool                             # Liaisons construites
cache.linking_stats: Dict[str, Any]                 # Statistiques de liaison
```

---

### **2. CacheManagerWithPricing** - Gestionnaire avec Tarification

Gestionnaire intermédiaire qui ajoute les capacités de tarification aux données OSM de base.

#### **Fonctionnalités**
- 💰 **Gestion des tarifs** : Prix par opérateur et catégorie
- 🏢 **Opérateurs français** : 15+ sociétés d'autoroutes
- 📊 **Calculs de coûts** : Péages ouverts et fermés
- 🎯 **Validation tarifaire** : Contrôles de cohérence

#### **Utilisation**
```python
from src.cache.managers.cache_manager_with_pricing import CacheManagerWithPricing

cache = CacheManagerWithPricing(data_dir="./data")
success = cache.load_all_with_pricing()

if success:
    # Calcul de coût pour un segment
    segment_cost = cache.calculate_segment_cost(
        operator="APRR",
        distance_km=45.2,
        vehicle_category="c1"
    )
    
    # Prix d'un péage ouvert
    toll_price = cache.get_open_toll_price("Fontaine Larivière", "c1")
    
    # Liste des opérateurs disponibles
    operators = cache.get_available_operators()
```

#### **Méthodes de tarification**
```python
# Coût au kilomètre (péages fermés)
cost_per_km = cache.get_operator_price_per_km(operator="ASF", category="c1")

# Tarif fixe (péages ouverts) 
fixed_price = cache.get_open_toll_price(toll_name="Crottet", category="c2")

# Validation des tarifs
is_valid = cache.validate_pricing_data()
```

---

### **3. OSMDataManager** - Données OpenStreetMap

Gestionnaire spécialisé dans le chargement et la validation des données OSM.

#### **Responsabilités**
- 🗺️ **Parsing OSM** : Lecture des fichiers GeoJSON
- ✅ **Validation géométrique** : Contrôle des coordonnées
- 🏷️ **Enrichissement** : Ajout de métadonnées
- 📦 **Sérialisation** : Cache des données parsées

#### **Utilisation**
```python
from src.cache.managers.osm_data_manager import OSMDataManager

osm_manager = OSMDataManager(data_dir="./data")

# Chargement des péages OSM
toll_booths = osm_manager.load_toll_booths()

# Chargement des segments autoroutiers
motorway_segments = osm_manager.load_motorway_segments()

# Validation des données
validation_result = osm_manager.validate_osm_data()
if not validation_result.is_valid:
    print("Erreurs OSM détectées:", validation_result.errors)
```

#### **Formats supportés**
```python
# Fichiers d'entrée attendus
data/osm/
├── toll_stations.geojson      # Péages avec propriétés OSM
├── motorway_segments.geojson  # Segments autoroutiers
└── motorway_junctions.geojson # Échangeurs (optionnel)
```

---

### **4. OpenTollsManager** - Péages Ouverts Spécialisés

Gestionnaire dédié aux péages ouverts avec tarifs fixes.

#### **Fonctionnalités**
- 🎯 **Péages ouverts uniquement** : Filtrage automatique
- 💶 **Tarifs fixes** : Gestion des prix par catégorie
- 🔍 **Recherche optimisée** : Index par nom et opérateur
- 📊 **Statistiques spécialisées** : Métriques des péages ouverts

#### **Utilisation**
```python
from src.cache.managers.open_tolls_manager import OpenTollsManager

open_manager = OpenTollsManager(data_dir="./data")
open_manager.load_open_tolls_data()

# Recherche par nom
toll = open_manager.find_toll_by_name("Fontaine Larivière")

# Tous les péages d'un opérateur
aprr_open_tolls = open_manager.get_tolls_by_operator("APRR")

# Calcul du coût total pour une liste de péages
total_cost = open_manager.calculate_total_cost(
    toll_names=["Crottet", "Mionnay", "Vichy"],
    vehicle_category="c1"
)
```

## 🔧 Utilisation avancée

### **Initialisation avec configuration personnalisée**
```python
# Configuration avancée
cache = CacheManagerWithLinking(
    data_dir="./data",
    cache_dir="custom_cache",
    max_linking_distance=1.5,  # Distance max pour liaisons (mètres)
    enable_statistics=True,     # Collecte de statistiques
    validate_on_load=True      # Validation automatique
)

# Chargement avec options
success = cache.load_all_including_motorway_linking(
    force_rebuild_links=False,  # Forcer la reconstruction des liaisons
    enable_toll_association=True,  # Associer péages aux segments
    save_cache=True            # Sauvegarder le cache après chargement
)
```

### **Accès aux statistiques détaillées**
```python
# Statistiques globales
global_stats = cache.get_comprehensive_statistics()
print(f"""
🗄️ Cache Statistics:
   - Toll booths loaded: {global_stats['toll_booths_count']}
   - Open tolls: {global_stats['open_tolls_count']}
   - Closed tolls: {global_stats['closed_tolls_count']}
   - Complete links: {global_stats['complete_links_count']}
   - Operators available: {global_stats['operators_count']}
   
⏱️ Performance:
   - Total loading time: {global_stats['total_loading_time_ms']}ms
   - Links building time: {global_stats['linking_time_ms']}ms
   - Memory usage: {global_stats['memory_usage_mb']}MB
""")
```

### **Gestion d'erreurs et validation**
```python
try:
    success = cache.load_all_including_motorway_linking()
    
    if not success:
        # Diagnostique des erreurs
        errors = cache.get_loading_errors()
        for error in errors:
            print(f"❌ {error['type']}: {error['message']}")
            print(f"   File: {error.get('file', 'N/A')}")
            print(f"   Details: {error.get('details', 'N/A')}")
    
    # Validation post-chargement
    validation = cache.validate_data_integrity()
    if not validation.is_valid:
        print("⚠️ Validation warnings:")
        for warning in validation.warnings:
            print(f"  - {warning}")
            
except Exception as e:
    print(f"💥 Critical error during cache loading: {e}")
    # Stratégie de fallback
    cache.load_minimal_data()  # Chargement minimal sans liaisons
```

### **Optimisation des performances**
```python
# Pré-chargement des index spatiaux
cache.preload_spatial_indexes()

# Cache des requêtes fréquentes
cache.enable_query_caching(max_cache_size=1000)

# Monitoring des performances
with cache.performance_monitor() as monitor:
    # Opérations critiques
    toll_booths = cache.find_tolls_near_route(coordinates)
    costs = cache.calculate_route_costs(segments)

# Résultats du monitoring
print(f"Query time: {monitor.total_time_ms}ms")
print(f"Cache hits: {monitor.cache_hits}/{monitor.total_queries}")
```

## 📊 Métriques de performance

### **Temps de chargement par gestionnaire**
- **OSMDataManager** : ~200-400ms (données OSM)
- **CacheManagerWithPricing** : ~600-900ms (+ tarifs)
- **CacheManagerWithLinking** : ~1200-1800ms (+ liaisons)

### **Utilisation mémoire typique**
- **Péages seuls** : ~2-3 MB
- **Avec tarifs** : ~3-4 MB  
- **Avec liaisons** : ~8-12 MB
- **Cache complet** : ~15-20 MB

### **Performances de requête**
- **Recherche péage par ID** : <1ms
- **Recherche spatiale** : 1-5ms
- **Calcul de coût** : <1ms
- **Construction liaison** : 10-50ms