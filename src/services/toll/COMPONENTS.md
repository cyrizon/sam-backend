# 📋 Composants Principaux - Optimisation des Péages

Cette documentation détaille les **composants principaux** du système d'optimisation simplifié des péages, leurs responsabilités et leurs interactions.

## 🎯 Vue d'ensemble

L'architecture simplifie le système d'optimisation des péages en se concentrant sur la **conformité aux contraintes** plutôt que sur l'optimisation complexe des coûts.

### 🏗️ Architecture des composants
```
┌─────────────────────────────────────────────────┐
│            SIMPLE TOLL OPTIMIZER                │  ← Orchestrateur principal
│  ┌─────────────────┐  ┌─────────────────────┐   │
│  │ Validation      │  │ Délégation unique   │   │
│  │ Paramètres      │  │ SimpleConstraint    │   │
│  └─────────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────┘
                        │
            ┌───────────┼───────────┐
            ▼                       ▼
┌─────────────────────┐    ┌─────────────────────┐
│ SIMPLE CONSTRAINT   │    │  ENHANCED CONSTRAINT│
│    STRATEGY         │    │     STRATEGY        │  ← Avec segmentation
│ (Priorités 1,2,3)   │    │  (Hybride + Seg.)   │
└─────────────────────┘    └─────────────────────┘
            │                       │
            ▼                       ▼
┌─────────────────────┐    ┌─────────────────────┐
│  TOLL FALLBACK      │    │   SEGMENTATION      │
│    STRATEGY         │    │     STRATEGY        │
│  (Route de base)    │    │  (Approche avancée) │
└─────────────────────┘    └─────────────────────┘
```

---

## 🚀 SimpleTollOptimizer

### 🎯 Rôle
**Orchestrateur principal** du système simplifié d'optimisation des péages avec délégation directe aux stratégies.

### 📋 Responsabilités
- **Validation des paramètres** : Vérification des coordonnées et contraintes
- **Délégation intelligente** : Choix entre stratégie simple ou améliorée
- **Gestion d'erreurs** : Centralisation du handling des erreurs
- **Performance tracking** : Suivi des métriques de performance
- **Configuration** : Application des paramètres globaux

### 🔄 Méthodes principales
```python
class SimpleTollOptimizer:
    def __init__(ors_service, use_segmentation=False)
    def compute_route_with_toll_limit(coordinates, max_tolls, **kwargs)
    def validate_request_parameters(coordinates, max_tolls)
    def delegate_to_strategy(strategy_params)
    def handle_computation_result(result, context)
```

### ⚡ Logique de délégation
```python
# Logique simplifiée - plus de sélection complexe de stratégie
if use_segmentation:
    return enhanced_constraint_strategy.find_routes(coordinates, max_tolls)
else:
    return simple_constraint_strategy.find_routes(coordinates, max_tolls)
```

### 🎯 Configuration
```python
class SimpleTollOptimizer:
    DEFAULT_TIMEOUT_MS = 5000
    ENABLE_PERFORMANCE_TRACKING = True
    DEFAULT_USE_SEGMENTATION = False
    FALLBACK_ON_TIMEOUT = True
```

---

## 🎯 SimpleConstraintStrategy

### 🎯 Rôle
**Stratégie principale** basée sur un système de priorités pour respecter les contraintes de péages.

### 📋 Responsabilités
- **Gestion des priorités** : Système à 3 niveaux de priorité
- **Tests de conformité** : Validation des contraintes max_tolls
- **Évitement intelligent** : Application d'avoid_features et polygones
- **Sélection optimale** : Choix des meilleures solutions par critère
- **Fallback automatique** : Délégation vers TollFallbackStrategy

### 🔄 Système de priorités
```python
# Priorité 1 : Solutions conformes (≤ max_tolls)
priority_1_routes = test_routes_with_constraints(coordinates, max_tolls)
if priority_1_routes:
    return select_best_solutions(priority_1_routes)

# Priorité 2 : Solutions backup (max_tolls + 1)  
priority_2_routes = test_routes_with_tolerance(coordinates, max_tolls + 1)
if priority_2_routes:
    return select_backup_solutions(priority_2_routes)

# Priorité 3 : Fallback
return toll_fallback_strategy.get_baseline_route(coordinates)
```

### ⚡ Méthodes de test
- **Test avec évitement** : `avoid_features: ["tollways"]`
- **Test standard** : Route normale avec localisation de péages
- **Test avec tolérance** : Backup avec max_tolls + 1
- **Validation contraintes** : Vérification finale du respect des limites

### 📊 Critères de sélection
- **Fastest** : Route la plus rapide dans la priorité
- **Cheapest** : Route la moins chère dans la priorité
- **Min_tolls** : Route avec minimum de péages dans la priorité

---

## 🔧 EnhancedConstraintStrategy

### 🎯 Rôle
**Stratégie hybride** combinant l'approche simple avec la segmentation avancée pour les cas complexes.

### 📋 Responsabilités
- **Approche hybride** : Simple d'abord, segmentation si échec
- **Segmentation intelligente** : Découpage en segments pour cas complexes
- **Optimisation avancée** : Techniques de segmentation et évitement progressif
- **Compatibilité** : Maintien de l'API et comportement de base
- **Performance** : Optimisation pour cas complexes sans impact sur cas simples

### 🔄 Logique hybride
```python
class EnhancedConstraintStrategy:
    def find_routes_with_constraints(coordinates, max_tolls):
        # Phase 1 : Approche simple classique
        simple_result = simple_constraint_strategy.find_routes(coordinates, max_tolls)
        
        if simple_result.is_successful():
            return simple_result
            
        # Phase 2 : Approche segmentation si échec
        if self.should_use_segmentation(coordinates, max_tolls):
            return segmentation_strategy.find_segmented_routes(coordinates, max_tolls)
            
        # Phase 3 : Fallback standard
        return fallback_strategy.get_baseline_route(coordinates)
```

### 🎯 Critères de segmentation
- **Échec de l'approche simple** : Aucune solution trouvée
- **Nombre de péages élevé** : max_tolls ≥ 3
- **Distance importante** : > 500km
- **Complexité géographique** : Nombreux péages sur le trajet

---

## 🆘 TollFallbackStrategy

### 🎯 Rôle
**Stratégie de repli** fournissant une solution de base quand aucune contrainte ne peut être respectée.

### 📋 Responsabilités
- **Route de base** : Calcul d'itinéraire sans contraintes
- **Localisation péages** : Identification des péages présents
- **Coût total** : Calcul du coût réel sans optimisation
- **Résultat uniforme** : fastest = cheapest = min_tolls
- **Statuts appropriés** : Codes d'erreur contextuels

### 🔄 Processus de fallback
```python
class TollFallbackStrategy:
    def get_baseline_route(coordinates, context="general"):
        # 1. Calcul route standard
        base_route = ors_service.calculate_route(coordinates)
        
        # 2. Localisation et coût des péages
        tolls = toll_finder.find_tolls_on_route(base_route)
        total_cost = sum(toll.cost for toll in tolls)
        
        # 3. Formatage uniforme
        result = {
            "fastest": base_route,
            "cheapest": base_route,  # Identique
            "min_tolls": base_route, # Identique
            "status": self.get_context_status(context, len(tolls))
        }
        
        return result
```

### 📊 Codes de statut contextuels
- `FALLBACK_NO_CONSTRAINTS` : Impossible de respecter contraintes
- `SOME_TOLLS_PRESENT` : Péages présents malgré évitement
- `GENERAL_STRATEGY` : Solution de base générique
- `COMPUTATION_TIMEOUT` : Timeout dépassé

---

## 🔧 Composants de Support

### 📊 RouteResultManager
**Gestion intelligente des résultats** avec sélection multi-critères
```python
class RouteResultManager:
    def select_best_fastest(candidates)
    def select_best_cheapest(candidates) 
    def select_best_min_tolls(candidates)
    def format_final_result(fastest, cheapest, min_tolls)
```

### 🛠️ RouteCalculator
**Calculs de routes** avec intégration ORS et localisation automatique des péages
```python
class RouteCalculator:
    def calculate_route_with_avoidance(coordinates, avoid_params)
    def calculate_standard_route(coordinates)
    def apply_toll_localization(route_data)
    def estimate_route_cost(route_geometry, tolls)
```

### ✅ RouteValidator  
**Validation des contraintes** et vérification de conformité
```python
class RouteValidator:
    def validate_toll_count_constraint(route, max_tolls)
    def validate_route_geometry(route_data)
    def check_avoidance_effectiveness(route, avoided_tolls)
    def verify_route_continuity(route_segments)
```

### ⚠️ TollErrorHandler
**Gestion centralisée des erreurs** avec logging contextualisé
```python
class TollErrorHandler:
    def handle_constraint_violation(max_tolls, actual_tolls)
    def handle_ors_service_error(error, context)
    def handle_timeout_error(timeout_ms, operation)
    def log_performance_metrics(operation, duration, success)
```

---

## 📈 Performance et Configuration

### ⚙️ TollOptimizationConfig
```python
class TollOptimizationConfig:
    # Timeouts
    MAX_COMPUTATION_TIME_MS = 5000
    SEGMENT_TIMEOUT_MS = 2000
    
    # Priorités
    ENABLE_BACKUP_PRIORITY = True
    BACKUP_TOLERANCE = 1
    
    # Performance
    ENABLE_EARLY_STOPPING = True
    ENABLE_ROUTE_CACHE = True
    MAX_PARALLEL_CALCULATIONS = 3
    
    # Segmentation
    AUTO_SEGMENTATION_THRESHOLD = 3  # max_tolls ≥ 3
    SEGMENTATION_DISTANCE_THRESHOLD = 500000  # 500km
```

### 📊 Métriques suivies
- **Temps de calcul** par stratégie et priorité
- **Taux de succès** par niveau de priorité
- **Distribution des solutions** (fastest/cheapest/min_tolls)
- **Efficacité des stratégies** (simple vs enhanced vs fallback)

### 🎯 Optimisations
- **Cache intelligent** : Réutilisation des calculs similaires
- **Arrêt anticipé** : Stop dès solution priorité 1 trouvée
- **Évitement sélectif** : Polygones optimisés pour performance
- **Délégation intelligente** : Choix automatique de la stratégie optimale

Les composants principaux garantissent une **architecture robuste** et **performante** pour l'optimisation simplifiée des péages, avec un **focus sur la conformité** aux contraintes plutôt que sur l'optimisation complexe.
