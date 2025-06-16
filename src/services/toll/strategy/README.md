# 🧠 Composants Spécialisés de Stratégie

Ce module contient les **composants spécialisés** utilisés par l'architecture simplifiée de gestion des péages pour des opérations précises et optimisées.

## 🎯 Vue d'ensemble

Les composants de ce module supportent le `SimpleTollOptimizer` et `SimpleConstraintStrategy` avec des fonctionnalités spécialisées :

- **RouteTester** : Tests et validation des routes selon différents critères
- **IntelligentAvoidance** : Logique d'évitement intelligent des péages
- **ExactTollFinder** : Localisation précise et analyse des péages
- **PriorityResolver** : Résolution des priorités et sélection des meilleures solutions
- **TollResponseService** : Service de formatage des réponses

---

## 🧪 RouteTester

### 🎯 Objectif
Tester et valider les routes selon différents critères de conformité aux contraintes de péages.

### 🔄 Fonctionnalités principales
```python
class RouteTester:
    def test_route_with_avoid_tolls(coordinates)
    def test_standard_route(coordinates) 
    def validate_toll_count(route, max_tolls)
    def test_route_compliance(route, constraints)
```

### ⚡ Algorithmes de test
- **Test avec évitement** : Utilise `avoid_features: ["tollways"]`
- **Test standard** : Route normale sans contraintes
- **Validation contraintes** : Vérification respect max_tolls
- **Tests de conformité** : Validation multi-critères

### 📊 Types de tests effectués
- ✅ **Route sans péage** : Évitement total réussi
- ⚠️ **Route avec péages limités** : Respect contrainte max_tolls
- ❌ **Route non conforme** : Trop de péages présents

---

## 🧠 IntelligentAvoidance

### 🎯 Objectif
Implémenter une logique d'évitement intelligent des péages avec optimisation géospatiale.

### 🔄 Fonctionnalités principales
```python
class IntelligentAvoidance:
    def create_avoidance_strategy(toll_locations)
    def apply_avoid_features(route_params)
    def optimize_avoidance_zones(tolls_to_avoid)
    def generate_smart_polygons(toll_data)
```

### ⚡ Stratégies d'évitement
1. **Évitement par features** : Utilisation des paramètres ORS
2. **Évitement par polygones** : Zones géographiques à éviter
3. **Évitement intelligent** : Combinaison des deux approches
4. **Optimisation géospatiale** : Minimisation des zones d'évitement

### 🎯 Optimisations implémentées
- **Polygones minimaux** : Zones d'évitement optimisées
- **Évitement sélectif** : Ciblage des péages spécifiques
- **Performance spatiale** : Calculs géométriques efficaces
- **Cache d'évitement** : Réutilisation des zones calculées

---

## 🔍 ExactTollFinder

### 🎯 Objectif
Localisation précise et analyse détaillée des péages sur les itinéraires calculés.

### 🔄 Fonctionnalités principales
```python
class ExactTollFinder:
    def find_tolls_on_route(route_geometry)
    def calculate_toll_costs(toll_list)
    def identify_toll_types(toll_info)
    def analyze_toll_distribution(route_data)
```

### ⚡ Algorithmes de localisation
1. **Intersection géospatiale** : Route vs base de données péages
2. **Calcul de coûts** : Prix selon type de véhicule et distance
3. **Classification** : Péages ouverts vs fermés vs barrières
4. **Distribution spatiale** : Analyse répartition sur l'itinéraire

### 📊 Types de péages identifiés
- **Système ouvert** : Tarif fixe à l'entrée (A1, A4, A13...)
- **Système fermé** : Tarif selon distance parcourue (A6, A7...)
- **Barrières** : Péages ponctuels (ponts, tunnels...)
- **Éco-taxe** : Péages écologiques spéciaux

### 🎯 Métriques calculées
- **Coût total** : Somme de tous les péages
- **Nombre de péages** : Comptage pour contraintes
- **Répartition** : Distribution géographique
- **Types dominants** : Analyse des systèmes de péage

---

## ⚖️ PriorityResolver

### 🎯 Objectif
Résolution des priorités et sélection des meilleures solutions selon les contraintes définies.

### 🔄 Fonctionnalités principales
```python
class PriorityResolver:
    def resolve_priority_1_solutions(routes_under_limit)
    def resolve_priority_2_backup(routes_at_limit_plus_one)
    def select_best_solutions(all_candidates)
    def apply_selection_criteria(routes, criteria)
```

### ⚡ Logique de résolution
1. **Priorité 1** : Routes avec ≤ max_tolls péages
2. **Priorité 2** : Routes avec max_tolls + 1 péages (backup)
3. **Priorité 3** : Fallback sans contraintes
4. **Sélection optimale** : Meilleurs fastest/cheapest/min_tolls

### 🎯 Critères de sélection
- **Fastest** : Route la plus rapide dans la priorité
- **Cheapest** : Route la moins chère dans la priorité
- **Min_tolls** : Route avec minimum de péages dans la priorité
- **Backup** : Solutions de secours acceptables

### 📊 Algorithme de priorité
```python
def resolve_best_solution_by_priority(candidates, max_tolls):
    priority_1 = [r for r in candidates if r.toll_count <= max_tolls]
    if priority_1:
        return select_optimal_from_priority_1(priority_1)
    
    priority_2 = [r for r in candidates if r.toll_count == max_tolls + 1]
    if priority_2:
        return select_best_backup(priority_2)
    
    return trigger_fallback_strategy()
```

---

## 🔧 TollResponseService

### 🎯 Objectif
Service de formatage et structuration des réponses pour l'API de péages.

### 🔄 Fonctionnalités principales
```python
class TollResponseService:
    def format_route_response(route_data, toll_info)
    def build_metadata(computation_info)
    def structure_toll_details(toll_list)
    def create_status_response(result_status)
```

### ⚡ Format de réponse structuré
```json
{
  "fastest": {
    "route": { /* GeoJSON */ },
    "cost": 8.50,
    "duration": 12000,
    "distance": 350000,
    "toll_count": 2,
    "tolls": [...]
  },
  "metadata": {
    "priority_used": 1,
    "algorithm_used": "simple_constraint",
    "computation_time_ms": 450
  }
}
```

### 🎯 Types de réponses
- **SUCCESS** : Solutions conformes trouvées
- **BACKUP** : Solutions de secours utilisées
- **FALLBACK** : Route de base sans contraintes
- **ERROR** : Erreurs de calcul ou validation

---

## 🔧 Utilisation des Composants

### 📋 Intégration avec SimpleConstraintStrategy
```python
# Test de routes
route_tester = RouteTester(ors_service)
avoid_route = route_tester.test_route_with_avoid_tolls(coordinates)

# Évitement intelligent
avoidance = IntelligentAvoidance()
strategy = avoidance.create_avoidance_strategy(toll_locations)

# Localisation de péages
toll_finder = ExactTollFinder()
tolls = toll_finder.find_tolls_on_route(route_geometry)

# Résolution de priorités
resolver = PriorityResolver()
best_solution = resolver.resolve_priority_1_solutions(candidates)

# Formatage de réponse
response_service = TollResponseService()
formatted_response = response_service.format_route_response(result)
```

### 🎯 Pipeline de traitement
1. **RouteTester** → Tests de conformité
2. **IntelligentAvoidance** → Stratégies d'évitement
3. **ExactTollFinder** → Localisation et coûts
4. **PriorityResolver** → Sélection optimale
5. **TollResponseService** → Formatage final

---

## 📈 Performance et Optimisations

### 🎯 Optimisations implémentées
- **Cache spatial** : Réutilisation des calculs géométriques
- **Évitement sélectif** : Ciblage précis des péages
- **Arrêt anticipé** : Stop dès solution priorité 1 trouvée
- **Calculs parallèles** : Tests multiples simultanés
- **Mémoire optimisée** : Structures de données efficaces

### 📊 Métriques de performance
- Temps de localisation des péages : < 100ms
- Temps de résolution des priorités : < 50ms
- Temps de formatage des réponses : < 20ms
- Mémoire utilisée : < 50MB par requête

### ⚙️ Configuration
```python
class StrategyConfig:
    ENABLE_SPATIAL_CACHE = True
    MAX_PARALLEL_TESTS = 3
    PRIORITY_TIMEOUT_MS = 2000
    RESPONSE_FORMAT_VERSION = "2.0"
```

Les composants spécialisés garantissent une **architecture modulaire** et des **performances optimisées** pour l'optimisation simplifiée des péages.
