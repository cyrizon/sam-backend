# 🚀 Services Optimization - Moteur d'Optimisation d'Itinéraires

## 📋 Vue d'ensemble

Le module `optimization` constitue le cœur de l'intelligence artificielle de routage SAM. Il implémente des algorithmes sophistiqués pour optimiser les itinéraires sous contraintes de péages et de budget, en utilisant une approche modulaire et évolutive.

## 🏗️ Architecture

```
src/services/optimization/
├── 📊 constants.py                 # Constantes spécialisées pour l'optimisation
├── 📁 route_optimization/          # Moteur principal d'optimisation
│   ├── 📁 main/                   # Orchestrateurs principaux
│   ├── 📁 route_handling/         # Gestion des routes de base
│   ├── 📁 toll_analysis/          # Analyse et sélection des péages
│   ├── 📁 segmentation/           # Segmentation et calcul des segments
│   ├── 📁 assembly/               # Assemblage des résultats finaux
│   └── 📁 utils/                  # Utilitaires d'optimisation
└── 📄 README.md                   # Documentation du module
```

## 🎯 Objectifs du système

### **Optimisation intelligente**
- 🧠 **Algorithmes adaptatifs** : Stratégies qui s'adaptent au contexte
- 🎯 **Multi-contraintes** : Péages, budget, temps, distance
- ⚡ **Performance** : Réponse rapide même pour routes complexes
- 🔄 **Évolutivité** : Architecture modulaire pour nouveaux algorithmes

### **Précision et fiabilité**
- 📊 **Analyse spatiale** : Détection précise des péages sur l'itinéraire
- 💰 **Calculs de coûts** : Intégration des tarifs réels français
- 🛣️ **Alternatives multiples** : Génération de plusieurs solutions optimales
- ✅ **Validation** : Vérification de la cohérence des résultats

## 🧩 Composant principal

### **TollOptimizationConfig** - Configuration Spécialisée

Configuration étendue héritant de `BaseOptimizationConfig` avec des paramètres spécifiques à l'optimisation de péages.

#### **Optimisation des coûts**
```python
from src.services.optimization.constants import TollOptimizationConfig

# Configuration de l'optimisation
EARLY_STOP_ZERO_COST = True        # Arrêt anticipé si coût nul trouvé
UNLIMITED_BASE_COST = float('inf')   # Coût de base illimité pour certains cas

# Utilisation dans les algorithmes
def optimize_route_cost(route_options):
    for route in route_options:
        if route.cost == 0 and TollOptimizationConfig.EARLY_STOP_ZERO_COST:
            return route  # Arrêt anticipé - route gratuite trouvée
```

#### **Détection de péages**
```python
# Configuration de la détection spatiale
TOLL_DETECTION_BUFFER_M = 80.0      # Buffer pour détecter les péages (80m)

# Utilisation dans l'analyse spatiale
def detect_tolls_on_route(route_geometry, toll_stations):
    buffer_m = TollOptimizationConfig.TOLL_DETECTION_BUFFER_M
    
    detected_tolls = []
    for toll in toll_stations:
        if route_geometry.distance(toll.geometry) <= buffer_m:
            detected_tolls.append(toll)
    
    return detected_tolls
```

#### **Noms d'opérations standardisés**
```python
# Classe pour le tracking de performance
class Operations:
    """Noms standardisés des opérations pour le tracking."""
    
    # Opérations principales
    COMPUTE_ROUTE_WITH_TOLL_LIMIT = "compute_route_with_toll_limit"
    COMPUTE_ROUTE_NO_TOLL = "compute_route_no_toll"
    COMPUTE_ROUTE_ONE_OPEN_TOLL = "compute_route_with_one_open_toll"
    COMPUTE_ROUTE_MANY_TOLLS = "compute_route_with_many_tolls"
    
    # Appels ORS
    ORS_BASE_ROUTE = "ORS_base_route"
    ORS_AVOID_TOLLWAYS = "ORS_avoid_tollways"
    ORS_ALTERNATIVE_ROUTE = "ORS_alternative_route"
    
    # Opérations sur les péages
    LOCATE_TOLLS = "locate_tolls"
    LOCATE_TOLLS_NO_TOLL = "locate_tolls_no_toll"
    LOCATE_TOLLS_ONE_TOLL = "locate_tolls_one_toll"
    LOCATE_TOLLS_MANY_TOLLS = "locate_tolls_many_tolls"
    LOCATE_TOLLS_FALLBACK = "locate_tolls_fallback"
    
    # Test de combinaisons
    PREPARE_TOLL_COMBINATIONS = "prepare_toll_combinations"
    TEST_TOLL_COMBINATIONS = "test_toll_combinations"
    TEST_SINGLE_COMBINATION = "test_single_combination"
    CREATE_AVOIDANCE_POLYGON = "create_avoidance_polygon"
    
    # Analyse de routes
    ANALYZE_ALTERNATIVE_ROUTE = "analyze_alternative_route"
```

### **Utilisation des opérations**
```python
from benchmark.performance_tracker import performance_tracker

# Tracking automatique des opérations
operation_name = TollOptimizationConfig.Operations.COMPUTE_ROUTE_WITH_TOLL_LIMIT

with performance_tracker.measure_operation(operation_name):
    result = compute_route_with_toll_limit(coordinates, max_tolls)
    performance_tracker.count_api_call(operation_name)
```

## 🏗️ Architecture du moteur d'optimisation

### **Pipeline d'optimisation en 8 étapes**

Le moteur `route_optimization` implémente un pipeline sophistiqué en 8 étapes modulaires :

```
1. 🔌 BaseRouteProvider     → Appel ORS initial avec info péages
2. 🔌 BaseRouteProvider     → Route alternative sans péages  
3. 🔍 TollIdentifier        → Identification des péages sur route
4. 📊 [Analyse interne]     → Évaluation des contraintes
5. 🎯 TollSelector          → Sélection des péages à éviter
6. 🔧 SegmentCreator        → Création des segments d'évitement
7. 📈 SegmentCalculator     → Calcul des routes alternatives
8. 🎨 RouteAssembler        → Assemblage des résultats finaux
```

### **Modules principaux**

#### **1. main/intelligent_optimizer.py**
```python
from src.services.optimization.route_optimization.main.intelligent_optimizer import IntelligentOptimizer

# Orchestrateur principal du pipeline
optimizer = IntelligentOptimizer(ors_service)

result = optimizer.find_optimized_route(
    coordinates=[[4.8345, 46.7123], [2.3522, 48.8566]],
    target_tolls=3,
    optimization_mode='count',
    veh_class="c1"
)
```

#### **2. route_handling/base_route_provider.py**
```python
# Étapes 1-2 : Fourniture des routes de base
provider = BaseRouteProvider(ors_service)

# Route avec péages
base_route = provider.get_base_route(coordinates)

# Route sans péages
no_toll_route = provider.get_no_toll_route(coordinates)
```

#### **3. toll_analysis/toll_identifier.py**
```python
# Étape 3 : Identification des péages
identifier = TollIdentifier()

tolls_on_route = identifier.identify_tolls_on_route(
    route_geometry=base_route.geometry,
    toll_stations=cache.toll_booths
)
```

#### **4. toll_analysis/toll_selector.py**
```python
# Étape 5 : Sélection des péages à éviter
selector = TollSelector()

selected_tolls = selector.select_tolls_to_avoid(
    available_tolls=tolls_on_route,
    target_count=target_tolls,
    optimization_mode='count',
    veh_class="c1"
)
```

#### **5. segmentation/segment_creator.py**
```python
# Étape 6 : Création des segments d'évitement
creator = SegmentCreator()

avoidance_segments = creator.create_avoidance_segments(
    tolls_to_avoid=selected_tolls,
    base_route=base_route
)
```

#### **6. segmentation/segment_calculator.py**
```python
# Étape 7 : Calcul des routes alternatives
calculator = SegmentCalculator(ors_service)

alternative_routes = calculator.calculate_alternative_routes(
    segments=avoidance_segments,
    coordinates=coordinates
)
```

#### **7. assembly/route_assembler.py**
```python
# Étape 8 : Assemblage des résultats
assembler = RouteAssembler()

final_result = assembler.assemble_final_results(
    base_route=base_route,
    no_toll_route=no_toll_route,
    alternative_routes=alternative_routes,
    optimization_context=context
)
```

## 🔧 Utilisation pratique

### **Optimisation par contrainte de péages**
```python
from src.services.optimization.route_optimization.main.intelligent_optimizer import IntelligentOptimizer
from src.services.ors_service import ORSService

# Initialisation
ors_service = ORSService()
optimizer = IntelligentOptimizer(ors_service)

# Optimisation avec limite de 2 péages
result = optimizer.find_optimized_route(
    coordinates=[[4.8345, 46.7123], [2.3522, 48.8566]],  # Lyon → Paris
    target_tolls=2,
    optimization_mode='count',
    veh_class="c1"
)

# Analyse du résultat
if result and result.get("status") == "SUCCESS":
    fastest = result["fastest"]
    cheapest = result["cheapest"]
    min_tolls = result["min_tolls"]
    
    print(f"Route la plus rapide : {fastest['duration']/3600:.1f}h, {fastest['cost']:.2f}€")
    print(f"Route la moins chère : {cheapest['duration']/3600:.1f}h, {cheapest['cost']:.2f}€")
    print(f"Route min péages : {min_tolls['toll_count']} péages, {min_tolls['cost']:.2f}€")
```

### **Optimisation par contrainte de budget**
```python
# Optimisation avec budget maximum
result = optimizer.find_optimized_route(
    coordinates=[[4.8345, 46.7123], [2.3522, 48.8566]],
    target_budget=25.00,  # 25€ maximum
    optimization_mode='budget',
    veh_class="c1"
)

# Vérification du respect du budget
if result and result.get("status") == "CONSTRAINT_RESPECTED":
    print("✅ Budget respecté")
    cheapest = result["cheapest"]
    print(f"Coût final : {cheapest['cost']:.2f}€ (≤ 25.00€)")
```

### **Configuration avancée**
```python
# Modification des paramètres d'optimisation
TollOptimizationConfig.TOLL_DETECTION_BUFFER_M = 120.0  # Buffer plus large
TollOptimizationConfig.EARLY_STOP_ZERO_COST = False     # Pas d'arrêt anticipé

# Lancement avec configuration personnalisée
result = optimizer.find_optimized_route(
    coordinates=coordinates,
    target_tolls=1,
    optimization_mode='count',
    veh_class="c2"  # Classe véhicule différente
)
```

## 📊 Monitoring et métriques

### **Tracking automatique**
```python
# Le système track automatiquement :
# - Durée totale d'optimisation
# - Nombre d'appels ORS
# - Combinaisons testées
# - Taux de succès par stratégie

# Résultat avec métriques
result = {
    "status": "SUCCESS",
    "fastest": {...},
    "cheapest": {...},
    "min_tolls": {...},
    "performance": {
        "total_duration_ms": 2847,
        "ors_calls": 3,
        "combinations_tested": 15,
        "cache_hits": 8,
        "strategy_used": "intelligent_v2"
    }
}
```

### **Opérations trackées**
```python
# Chaque opération est automatiquement trackée
Operations = TollOptimizationConfig.Operations

# Exemples d'opérations monitorées :
# - compute_route_with_toll_limit
# - locate_tolls_many_tolls  
# - test_toll_combinations
# - create_avoidance_polygon
# - analyze_alternative_route
```

## 🛠️ Extension du système

### **Ajout de nouvelles stratégies**
```python
# Nouvelle stratégie d'optimisation
class TimeOptimizedStrategy:
    def optimize(self, routes, constraints):
        # Logique d'optimisation par temps
        return optimized_routes

# Intégration dans l'optimiseur
optimizer.add_strategy('time_optimized', TimeOptimizedStrategy())
```

### **Nouveaux critères d'optimisation**
```python
# Extension des constantes
class TollOptimizationConfig(BaseOptimizationConfig):
    # Nouvelles constantes
    TIME_OPTIMIZATION_WEIGHT = 0.7
    DISTANCE_OPTIMIZATION_WEIGHT = 0.3
    
    class Operations:
        # Nouvelles opérations
        OPTIMIZE_BY_TIME = "optimize_by_time"
        OPTIMIZE_BY_DISTANCE = "optimize_by_distance"
```